"""
Claude Agent - Agent Orchestrator
Integração com Claude Code CLI para execução de tarefas complexas
"""

import asyncio
import subprocess
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..models.task import Task, TaskResult
from ..utils.logger import logger


@dataclass
class ClaudeConfig:
    """Configuração do agente Claude"""
    api_key: Optional[str] = None
    retry_attempts: int = 3
    max_tokens: int = 4000
    temperature: float = 0.1
    skip_permissions: bool = True
    personas: Dict[str, str] = None
    
    def __post_init__(self):
        if self.personas is None:
            self.personas = {
                "sm": "/BMad:agents:sm",
                "dev": "/BMad:agents:dev", 
                "qa": "/BMad:agents:qa",
                "pm": "/BMad:agents:pm",
                "po": "/BMad:agents:po"
            }


class ClaudeAgent:
    """Agente Claude Code para execução de tarefas complexas"""
    
    def __init__(self, config: Optional[ClaudeConfig] = None):
        self.config = config or ClaudeConfig()
        self.logger = logger
        self._validate_installation()
        self._setup_environment()
    
    def _validate_installation(self):
        """Valida se Claude Code está instalado"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("✅ Claude Code CLI encontrado")
            else:
                raise RuntimeError("Claude Code CLI não está funcionando")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude Code CLI não encontrado. "
                "Instale com: npm install -g @anthropic-ai/claude-code"
            )
    
    def _setup_environment(self):
        """Configura ambiente para Claude Code"""
        # Verificar API key (opcional - não é obrigatória)
        if not self.config.api_key:
            api_key = self._get_api_key_from_env()
            if api_key:
                self.config.api_key = api_key
            else:
                self.logger.info(
                    "✅ Claude Code configurado sem API key (autenticação local)"
                )
        
        # Verificar BMAD-METHOD
        self._validate_bmad_method()
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Obtém API key do ambiente"""
        import os
        return os.getenv("ANTHROPIC_API_KEY")
    
    def _validate_bmad_method(self):
        """Valida se BMAD-METHOD está configurado"""
        try:
            # Testar uma persona básica
            result = subprocess.run(
                ["claude", "/BMad:agents:dev", "teste"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("✅ BMAD-METHOD configurado")
            else:
                self.logger.warning("⚠️ BMAD-METHOD pode não estar configurado corretamente")
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao validar BMAD-METHOD: {str(e)}")
    
    async def execute_task(self, task: Task, context: Dict[str, Any] = None) -> TaskResult:
        """
        Executa uma task usando Claude Code
        
        Args:
            task: Task a ser executada
            context: Contexto adicional da task
            
        Returns:
            TaskResult: Resultado da execução
        """
        start_time = time.time()
        self.logger.info(f"🤖 Claude executando task: {task.id}")
        
        try:
            # Determinar persona baseada na task
            persona = self._select_persona(task)
            
            # Criar prompt para Claude
            prompt = self._create_prompt(task, context)
            
            # Executar com Claude
            result = await self._execute_with_claude(prompt, persona)
            
            execution_time = time.time() - start_time
            
            # Processar resultado
            task_result = self._process_result(result, task, execution_time)
            
            self.logger.info(f"✅ Claude completou task {task.id} em {execution_time:.2f}s")
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Erro na execução da task {task.id}: {str(e)}")
            
            return TaskResult(
                success=False,
                message=f"Erro na execução: {str(e)}",
                error=str(e),
                execution_time=execution_time,
                agent_used="claude"
            )
    
    def _select_persona(self, task: Task) -> str:
        """Seleciona persona baseada na task"""
        # Mapear tipo de task para persona
        task_type = task.title.lower()
        
        if any(word in task_type for word in ["test", "qa", "quality"]):
            return "qa"
        elif any(word in task_type for word in ["plan", "sprint", "organize"]):
            return "sm"
        elif any(word in task_type for word in ["analyze", "product", "requirement"]):
            return "po"
        elif any(word in task_type for word in ["manage", "coordinate", "timeline"]):
            return "pm"
        else:
            return "dev"  # Padrão para desenvolvimento
    
    def _create_prompt(self, task: Task, context: Optional[Dict[str, Any]] = None) -> str:
        """Cria prompt detalhado para Claude"""
        prompt = f"""
Você é um desenvolvedor experiente usando Claude Code para implementar uma tarefa.

=== TAREFA ===
ID: {task.id}
Título: {task.title}
Descrição: {task.description}
Prioridade: {task.priority}
Complexidade: {task.complexity}

=== CRITÉRIOS DE ACEITE ===
"""
        
        # Adicionar critérios de aceite
        if hasattr(task, 'acceptance_criteria') and task.acceptance_criteria:
            for i, criteria in enumerate(task.acceptance_criteria, 1):
                prompt += f"{i}. {criteria}\n"
        else:
            prompt += "Implementar funcionalidade conforme especificação\n"
        
        # Adicionar contexto se disponível
        if context:
            prompt += f"\n=== CONTEXTO ADICIONAL ===\n"
            for key, value in context.items():
                prompt += f"{key}: {value}\n"
        
        prompt += """

=== INSTRUÇÕES ===
1. Analise a tarefa e seus critérios de aceite
2. Implemente a funcionalidade solicitada
3. Siga as melhores práticas de desenvolvimento
4. Adicione testes quando apropriado
5. Documente o código gerado
6. Valide que todos os critérios foram atendidos

=== RESULTADO ESPERADO ===
- Código funcional e bem documentado
- Testes adequados
- Documentação atualizada
- Critérios de aceite atendidos

Execute esta tarefa agora.
"""
        
        return prompt
    
    async def _execute_with_claude(self, prompt: str, persona: str) -> Dict[str, Any]:
        """Executa comando com Claude Code"""
        # Construir comando
        persona_prefix = self.config.personas.get(persona, self.config.personas["dev"])
        full_prompt = f"{persona_prefix} {prompt}"
        
        claude_command = ["claude"]
        
        # Adicionar flag de skip permissions se configurado
        if self.config.skip_permissions:
            claude_command.append("--dangerously-skip-permissions")
        
        claude_command.append(full_prompt)
        
        self.logger.info(f"🤖 Executando com persona: {persona}")
        
        # Executar comando
        process = await asyncio.create_subprocess_exec(
            *claude_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd()
        )
        
        try:
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "return_code": process.returncode,
                "persona": persona
            }
            
        except Exception as e:
            process.kill()
            raise Exception(f"Erro na execução do Claude: {str(e)}")
    
    def _process_result(self, result: Dict[str, Any], task: Task, execution_time: float) -> TaskResult:
        """Processa resultado da execução"""
        if result["success"]:
            # Extrair informações úteis do output
            output = result["stdout"]
            
            # Detectar arquivos criados/modificados
            files_created = self._extract_files_created(output)
            
            # Detectar código gerado
            code_generated = self._detect_code_generation(output)
            
            # Detectar testes
            tests_created = self._detect_tests_creation(output)
            
            return TaskResult(
                success=True,
                message=f"Task executada com sucesso usando persona {result['persona']}",
                data={
                    "files_created": files_created,
                    "code_generated": code_generated,
                    "tests_created": tests_created,
                    "persona_used": result["persona"],
                    "output_length": len(output)
                },
                execution_time=execution_time,
                agent_used="claude"
            )
        else:
            return TaskResult(
                success=False,
                message=f"Claude falhou com código {result['return_code']}",
                error=result["stderr"],
                execution_time=execution_time,
                agent_used="claude"
            )
    
    def _extract_files_created(self, output: str) -> List[str]:
        """Extrai arquivos criados do output"""
        files = []
        
        # Padrões para detectar arquivos criados
        patterns = [
            r"criado arquivo:?\s*([^\n]+)",
            r"criando:?\s*([^\n]+)",
            r"arquivo:?\s*([^\n]+\.(py|js|ts|java|cpp|h|md|txt|json|yaml|yml))",
            r"```([^\n]+\.(py|js|ts|java|cpp|h|md|txt|json|yaml|yml))"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    files.append(match[0])
                else:
                    files.append(match)
        
        return list(set(files))  # Remove duplicatas
    
    def _detect_code_generation(self, output: str) -> bool:
        """Detecta se código foi gerado"""
        code_indicators = [
            "```python", "```javascript", "```typescript", "```java",
            "```cpp", "```c", "```go", "```rust", "```php",
            "def ", "function ", "class ", "public ", "private ",
            "import ", "export ", "require(", "from "
        ]
        
        return any(indicator in output for indicator in code_indicators)
    
    def _detect_tests_creation(self, output: str) -> bool:
        """Detecta se testes foram criados"""
        test_indicators = [
            "test_", "Test", "describe(", "it(", "assert", "expect(",
            "pytest", "unittest", "jest", "mocha", "junit"
        ]
        
        return any(indicator in output for indicator in test_indicators)
    
    async def test_connection(self) -> bool:
        """Testa conexão com Claude Code"""
        try:
            result = await self._execute_with_claude(
                "Responda apenas 'OK' se estiver funcionando.",
                "dev"
            )
            return result["success"]
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de conexão: {str(e)}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades do agente"""
        return {
            "name": "Claude Code",
            "type": "complex_tasks",
            "personas": list(self.config.personas.keys()),
            "retry_attempts": self.config.retry_attempts,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso"""
        # Por enquanto, retorna dados básicos
        # TODO: Implementar tracking real de uso
        return {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "personas_used": {}
        } 