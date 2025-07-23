"""
Gemini Agent - Agent Orchestrator
Integração com Gemini CLI para execução rápida de tarefas
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
class GeminiConfig:
    """Configuração do agente Gemini"""
    api_key: Optional[str] = None  # NÃO USAR - deixar Gemini usar auth padrão
    retry_attempts: int = 2
    max_tokens: int = 2000
    temperature: float = 0.2
    model: str = "gemini-2.5-pro"  # Modelo padrão do Gemini CLI
    mcp_servers: List[str] = None
    
    def __post_init__(self):
        if self.mcp_servers is None:
            self.mcp_servers = [
                "filesystem",
                "git",
                "github",
                "terminal"
            ]


class GeminiAgent:
    """Agente Gemini CLI para execução rápida de tarefas"""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        self.logger = logger
        self._validate_installation()
        self._setup_environment()
    
    def _validate_installation(self):
        """Valida se Gemini CLI está instalado"""
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("✅ Gemini CLI encontrado")
            else:
                raise RuntimeError("Gemini CLI não está funcionando")
        except FileNotFoundError:
            raise RuntimeError(
                "Gemini CLI não encontrado. "
                "Instale com: npm install -g @google/gemini-cli"
            )
    
    def _setup_environment(self):
        """Configura ambiente para Gemini CLI"""
        # NÃO carregar API key - usar autenticação padrão do Gemini CLI
        self.logger.info(
            "✅ Gemini CLI configurado com autenticação padrão"
        )
        
        # Verificar MCP servers
        self._validate_mcp_servers()
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """DEPRECATED: Não usar API key - deixar Gemini CLI usar sua autenticação padrão"""
        return None
    
    def _validate_mcp_servers(self):
        """Valida se MCP servers estão disponíveis"""
        try:
            # Testar comando básico
            result = subprocess.run(
                ["gemini", "teste"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.info("✅ Gemini CLI configurado")
            else:
                self.logger.warning("⚠️ Gemini CLI pode não estar configurado corretamente")
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao validar Gemini CLI: {str(e)}")
    
    async def execute_task(self, task: Task, context: Dict[str, Any] = None) -> TaskResult:
        """
        Executa uma task usando Gemini CLI
        
        Args:
            task: Task a ser executada
            context: Contexto adicional da task
            
        Returns:
            TaskResult: Resultado da execução
        """
        start_time = time.time()
        self.logger.info(f"🤖 Gemini executando task: {task.id}")
        
        try:
            # Criar prompt otimizado para Gemini
            prompt = self._create_prompt(task, context)
            
            # Executar com Gemini
            result = await self._execute_with_gemini(prompt)
            
            execution_time = time.time() - start_time
            
            # Processar resultado
            task_result = self._process_result(result, task, execution_time)
            
            self.logger.info(f"✅ Gemini completou task {task.id} em {execution_time:.2f}s")
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Erro na execução da task {task.id}: {str(e)}")
            
            return TaskResult(
                success=False,
                message=f"Erro na execução: {str(e)}",
                error=str(e),
                execution_time=execution_time,
                agent_used="gemini"
            )
    
    def _create_prompt(self, task: Task, context: Optional[Dict[str, Any]] = None) -> str:
        """Cria prompt otimizado para Gemini"""
        prompt = f"""
Você é um desenvolvedor experiente usando Gemini para implementar uma tarefa rapidamente.

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
1. Analise a tarefa rapidamente
2. Implemente a funcionalidade de forma eficiente
3. Use MCP servers quando apropriado (filesystem, git, terminal)
4. Foque na implementação prática
5. Valide que os critérios foram atendidos

=== RESULTADO ESPERADO ===
- Implementação funcional
- Código limpo e eficiente
- Critérios de aceite atendidos

Execute esta tarefa agora de forma rápida e eficiente.
"""
        
        return prompt
    
    async def _execute_with_gemini(self, prompt: str) -> Dict[str, Any]:
        """Executa comando com Gemini CLI"""
        # Construir comando usando a sintaxe correta do Gemini CLI
        gemini_command = ["gemini", "--prompt", prompt]
        
        # NÃO adicionar --yolo pois não é uma flag válida
        # Deixar o Gemini usar suas configurações padrão
        
        self.logger.info(f"🤖 Executando com modelo padrão do Gemini CLI")
        
        # Executar comando
        process = await asyncio.create_subprocess_exec(
            *gemini_command,
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
                "model": "gemini-2.5-pro"  # Modelo padrão do CLI
            }
            
        except Exception as e:
            process.kill()
            raise Exception(f"Erro na execução do Gemini: {str(e)}")
    
    def _process_result(self, result: Dict[str, Any], task: Task, execution_time: float) -> TaskResult:
        """Processa resultado da execução"""
        if result["success"]:
            # Extrair informações úteis do output
            output = result["stdout"]
            
            # Detectar arquivos criados/modificados
            files_created = self._extract_files_created(output)
            
            # Detectar código gerado
            code_generated = self._detect_code_generation(output)
            
            # Detectar uso de MCP servers
            mcp_usage = self._detect_mcp_usage(output)
            
            return TaskResult(
                success=True,
                message=f"Task executada com sucesso usando modelo {result['model']}",
                data={
                    "files_created": files_created,
                    "code_generated": code_generated,
                    "mcp_usage": mcp_usage,
                    "model_used": result["model"],
                    "output_length": len(output)
                },
                execution_time=execution_time,
                agent_used="gemini"
            )
        else:
            return TaskResult(
                success=False,
                message=f"Gemini falhou com código {result['return_code']}",
                error=result["stderr"],
                execution_time=execution_time,
                agent_used="gemini"
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
    
    def _detect_mcp_usage(self, output: str) -> List[str]:
        """Detecta uso de MCP servers"""
        mcp_servers_used = []
        
        for server in self.config.mcp_servers:
            if server in output.lower():
                mcp_servers_used.append(server)
        
        return mcp_servers_used
    
    async def test_connection(self) -> bool:
        """Testa conexão com Gemini CLI"""
        try:
            result = await self._execute_with_gemini(
                "Responda apenas 'OK' se estiver funcionando."
            )
            return result["success"]
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de conexão: {str(e)}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades do agente"""
        return {
            "name": "Gemini CLI",
            "type": "fast_tasks",
            "model": self.config.model,
            "retry_attempts": self.config.retry_attempts,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "mcp_servers": self.config.mcp_servers
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
            "models_used": {},
            "mcp_usage": {}
        } 