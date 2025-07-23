# Arquitetura Técnica - Agent Orchestrator

## 🎯 Visão da Arquitetura

### Princípios Arquiteturais
1. **Clean Architecture**: Separação clara de responsabilidades
2. **SOLID Principles**: Código modular e extensível
3. **Dependency Injection**: Baixo acoplamento
4. **Event-Driven**: Comunicação assíncrona
5. **Fail-Fast**: Detecção rápida de problemas
6. **Observability**: Logs, métricas e traces

## 🏗️ Estrutura do Projeto

```
agent_orchestrator/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── analyze.py
│   │   ├── execute.py
│   │   ├── sprint.py
│   │   └── status.py
│   ├── parser.py
│   └── help.py
├── core/
│   ├── __init__.py
│   ├── engine.py
│   ├── orchestrator.py
│   ├── scheduler.py
│   └── validator.py
├── agents/
│   ├── __init__.py
│   ├── base.py
│   ├── claude.py
│   ├── gemini.py
│   ├── factory.py
│   └── registry.py
├── parsers/
│   ├── __init__.py
│   ├── backlog.py
│   ├── sprint.py
│   └── task.py
├── templates/
│   ├── __init__.py
│   ├── web_dev.py
│   ├── api_dev.py
│   ├── mobile_dev.py
│   └── data_science.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── config.py
│   ├── file_utils.py
│   └── validation.py
├── models/
│   ├── __init__.py
│   ├── backlog.py
│   ├── sprint.py
│   ├── task.py
│   └── agent.py
├── exceptions/
│   ├── __init__.py
│   ├── agent_exceptions.py
│   ├── parser_exceptions.py
│   └── orchestration_exceptions.py
└── constants/
    ├── __init__.py
    ├── commands.py
    ├── agents.py
    └── templates.py
```

## 🔧 Padrões de Design

### 1. Command Pattern (CLI)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class CommandResult:
    success: bool
    message: str
    data: Dict[str, Any] = None

class Command(ABC):
    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> CommandResult:
        pass

class AnalyzeCommand(Command):
    def execute(self, args: Dict[str, Any]) -> CommandResult:
        try:
            # Implementação da análise de backlog
            return CommandResult(success=True, message="Backlog analisado com sucesso")
        except Exception as e:
            return CommandResult(success=False, message=f"Erro: {str(e)}")
```

### 2. Factory Pattern (Agentes)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class AgentType(Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"

class Agent(ABC):
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def can_handle(self, task: Dict[str, Any]) -> bool:
        pass

class ClaudeAgent(Agent):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Implementação específica do Claude
        pass
    
    def can_handle(self, task: Dict[str, Any]) -> bool:
        # Lógica para determinar se pode executar a tarefa
        return task.get("complexity", "low") == "high"

class AgentFactory:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def create_agent(self, agent_type: AgentType) -> Agent:
        if agent_type == AgentType.CLAUDE:
            return ClaudeAgent(self.config["claude_api_key"])
        elif agent_type == AgentType.GEMINI:
            return GeminiAgent(self.config["gemini_api_key"])
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

### 3. Strategy Pattern (Orquestração)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class OrchestrationStrategy(ABC):
    @abstractmethod
    async def orchestrate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass

class SequentialStrategy(OrchestrationStrategy):
    async def orchestrate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for task in tasks:
            result = await self._execute_task(task)
            results.append(result)
        return {"strategy": "sequential", "results": results}

class ParallelStrategy(OrchestrationStrategy):
    async def orchestrate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        import asyncio
        tasks_coroutines = [self._execute_task(task) for task in tasks]
        results = await asyncio.gather(*tasks_coroutines)
        return {"strategy": "parallel", "results": results}
```

### 4. Repository Pattern (I/O)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

class BacklogRepository(ABC):
    @abstractmethod
    async def read(self, path: Path) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def write(self, path: Path, data: Dict[str, Any]) -> bool:
        pass

class FileBacklogRepository(BacklogRepository):
    async def read(self, path: Path) -> Dict[str, Any]:
        import aiofiles
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
        return self._parse_markdown(content)
    
    async def write(self, path: Path, data: Dict[str, Any]) -> bool:
        import aiofiles
        content = self._serialize_markdown(data)
        async with aiofiles.open(path, 'w') as f:
            await f.write(content)
        return True
```

## 🎯 Modelos de Dados

### 1. Backlog Model
```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class UserStory(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: int
    priority: str
    dependencies: List[str] = []
    created_at: datetime
    updated_at: datetime

class Backlog(BaseModel):
    id: str
    title: str
    description: str
    user_stories: List[UserStory]
    total_points: int
    created_at: datetime
    updated_at: datetime
```

### 2. Sprint Model
```python
class Sprint(BaseModel):
    id: str
    name: str
    description: str
    user_stories: List[UserStory]
    max_points: int
    start_date: datetime
    end_date: datetime
    status: str  # "planned", "in_progress", "completed"
    velocity: Optional[float] = None
```

### 3. Task Model
```python
class Task(BaseModel):
    id: str
    title: str
    description: str
    user_story_id: str
    agent_type: str
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
```

## 🔄 Fluxo de Dados

### 1. Análise de Backlog
```python
class BacklogAnalyzer:
    def __init__(self, parser: BacklogParser, validator: BacklogValidator):
        self.parser = parser
        self.validator = validator
    
    async def analyze(self, file_path: Path) -> Backlog:
        # 1. Ler arquivo
        content = await self.parser.read(file_path)
        
        # 2. Parse markdown
        parsed_data = self.parser.parse(content)
        
        # 3. Validar estrutura
        self.validator.validate(parsed_data)
        
        # 4. Criar modelo
        backlog = Backlog(**parsed_data)
        
        # 5. Calcular métricas
        backlog.total_points = sum(story.story_points for story in backlog.user_stories)
        
        return backlog
```

### 2. Geração de Sprint
```python
class SprintGenerator:
    def __init__(self, strategy: SprintGenerationStrategy):
        self.strategy = strategy
    
    async def generate(self, backlog: Backlog, max_points: int) -> Sprint:
        # 1. Selecionar stories baseado na estratégia
        selected_stories = self.strategy.select_stories(backlog.user_stories, max_points)
        
        # 2. Validar dependências
        self._validate_dependencies(selected_stories)
        
        # 3. Criar sprint
        sprint = Sprint(
            id=f"SPRINT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            name=f"Sprint {datetime.now().strftime('%Y-%m-%d')}",
            user_stories=selected_stories,
            max_points=max_points,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            status="planned"
        )
        
        return sprint
```

### 3. Execução de Tarefa
```python
class TaskExecutor:
    def __init__(self, agent_factory: AgentFactory, logger: Logger):
        self.agent_factory = agent_factory
        self.logger = logger
    
    async def execute(self, task: Task) -> TaskResult:
        try:
            # 1. Selecionar agente
            agent = self._select_agent(task)
            
            # 2. Preparar dados
            task_data = self._prepare_task_data(task)
            
            # 3. Executar
            start_time = time.time()
            result = await agent.execute(task_data)
            execution_time = time.time() - start_time
            
            # 4. Validar resultado
            self._validate_result(result)
            
            # 5. Atualizar task
            task.status = "completed"
            task.result = result
            task.execution_time = execution_time
            task.completed_at = datetime.now()
            
            return TaskResult(success=True, data=result)
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.logger.error(f"Task {task.id} failed: {str(e)}")
            return TaskResult(success=False, error=str(e))
```

## 🔧 Componentes Core

### 1. Core Engine
```python
class OrchestratorEngine:
    def __init__(
        self,
        agent_factory: AgentFactory,
        backlog_analyzer: BacklogAnalyzer,
        sprint_generator: SprintGenerator,
        task_executor: TaskExecutor,
        logger: Logger
    ):
        self.agent_factory = agent_factory
        self.backlog_analyzer = backlog_analyzer
        self.sprint_generator = sprint_generator
        self.task_executor = task_executor
        self.logger = logger
    
    async def analyze_backlog(self, file_path: Path) -> Backlog:
        """Analisa um arquivo de backlog"""
        self.logger.info(f"Analisando backlog: {file_path}")
        backlog = await self.backlog_analyzer.analyze(file_path)
        self.logger.info(f"Backlog analisado: {len(backlog.user_stories)} stories")
        return backlog
    
    async def generate_sprint(self, backlog: Backlog, max_points: int) -> Sprint:
        """Gera um sprint baseado no backlog"""
        self.logger.info(f"Gerando sprint com {max_points} pontos")
        sprint = await self.sprint_generator.generate(backlog, max_points)
        self.logger.info(f"Sprint gerado: {len(sprint.user_stories)} stories")
        return sprint
    
    async def execute_task(self, task_id: str, sprint: Sprint) -> TaskResult:
        """Executa uma tarefa específica"""
        task = self._find_task(task_id, sprint)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} não encontrada")
        
        self.logger.info(f"Executando task: {task_id}")
        return await self.task_executor.execute(task)
```

### 2. CLI Interface
```python
import click
from pathlib import Path
from typing import Dict, Any

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Agent Orchestrator - Orquestrador de Agentes de IA"""
    pass

@cli.command()
@click.argument('backlog_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Arquivo de saída')
def analyze(backlog_file: str, output: str):
    """Analisa um arquivo de backlog"""
    try:
        engine = get_orchestrator_engine()
        backlog = await engine.analyze_backlog(Path(backlog_file))
        
        if output:
            save_backlog(backlog, output)
        else:
            print_backlog_summary(backlog)
            
    except Exception as e:
        click.echo(f"Erro: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('task_id')
@click.option('--sprint', '-s', help='Arquivo de sprint')
def execute(task_id: str, sprint: str):
    """Executa uma tarefa específica"""
    try:
        engine = get_orchestrator_engine()
        sprint_data = load_sprint(sprint) if sprint else None
        
        result = await engine.execute_task(task_id, sprint_data)
        
        if result.success:
            click.echo(f"Task {task_id} executada com sucesso")
            print_task_result(result.data)
        else:
            click.echo(f"Erro na execução: {result.error}", err=True)
            
    except Exception as e:
        click.echo(f"Erro: {str(e)}", err=True)
        sys.exit(1)
```

## 🔒 Segurança e Validação

### 1. Validação de Input
```python
from pydantic import BaseModel, validator
import re

class TaskInput(BaseModel):
    task_id: str
    parameters: Dict[str, Any]
    
    @validator('task_id')
    def validate_task_id(cls, v):
        if not re.match(r'^TASK-\d+$', v):
            raise ValueError('Task ID deve seguir o padrão TASK-XXX')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        # Validar parâmetros perigosos
        dangerous_keys = ['exec', 'eval', 'system']
        for key in dangerous_keys:
            if key in str(v).lower():
                raise ValueError(f'Parâmetro perigoso detectado: {key}')
        return v
```

### 2. Sanitização de Dados
```python
class InputSanitizer:
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitiza caminhos de arquivo"""
        # Remove caracteres perigosos
        dangerous_chars = r'[<>:"|?*]'
        return re.sub(dangerous_chars, '', path)
    
    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitiza comandos"""
        # Remove caracteres de injeção
        injection_chars = r'[;&|`$]'
        return re.sub(injection_chars, '', command)
```

## 📊 Logging e Observabilidade

### 1. Structured Logging
```python
import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Configurar handler para JSON
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_execution(self, operation: str, duration: float, success: bool, **kwargs):
        """Log estruturado de execução"""
        log_entry = {
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_error(self, operation: str, error: str, **kwargs):
        """Log de erro estruturado"""
        log_entry = {
            "operation": operation,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.error(json.dumps(log_entry))
```

### 2. Métricas
```python
from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None

class MetricsCollector:
    def __init__(self):
        self.metrics: List[Metric] = []
    
    def record_execution_time(self, operation: str, duration: float, **tags):
        """Registra tempo de execução"""
        metric = Metric(
            name=f"{operation}_execution_time",
            value=duration,
            timestamp=datetime.now(),
            tags=tags
        )
        self.metrics.append(metric)
    
    def record_success_rate(self, operation: str, success: bool, **tags):
        """Registra taxa de sucesso"""
        metric = Metric(
            name=f"{operation}_success_rate",
            value=1.0 if success else 0.0,
            timestamp=datetime.now(),
            tags=tags
        )
        self.metrics.append(metric)
    
    def get_average_time(self, operation: str) -> float:
        """Calcula tempo médio de execução"""
        operation_metrics = [
            m for m in self.metrics 
            if m.name == f"{operation}_execution_time"
        ]
        if not operation_metrics:
            return 0.0
        return sum(m.value for m in operation_metrics) / len(operation_metrics)
```

## 🧪 Testabilidade

### 1. Testes Unitários
```python
import pytest
from unittest.mock import Mock, AsyncMock
from agent_orchestrator.core.engine import OrchestratorEngine

class TestOrchestratorEngine:
    @pytest.fixture
    def mock_components(self):
        return {
            'agent_factory': Mock(),
            'backlog_analyzer': Mock(),
            'sprint_generator': Mock(),
            'task_executor': Mock(),
            'logger': Mock()
        }
    
    @pytest.fixture
    def engine(self, mock_components):
        return OrchestratorEngine(**mock_components)
    
    @pytest.mark.asyncio
    async def test_analyze_backlog_success(self, engine, mock_components):
        # Arrange
        mock_backlog = Mock()
        mock_components['backlog_analyzer'].analyze.return_value = mock_backlog
        
        # Act
        result = await engine.analyze_backlog(Path("test.md"))
        
        # Assert
        mock_components['backlog_analyzer'].analyze.assert_called_once_with(Path("test.md"))
        assert result == mock_backlog
```

### 2. Testes de Integração
```python
class TestAgentIntegration:
    @pytest.mark.asyncio
    async def test_claude_agent_execution(self):
        # Arrange
        agent = ClaudeAgent("test_api_key")
        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test description",
            user_story_id="US-001",
            agent_type="claude"
        )
        
        # Act
        result = await agent.execute(task.dict())
        
        # Assert
        assert result is not None
        assert "output" in result
```

## 🚀 Performance e Otimização

### 1. Async/Await
```python
import asyncio
from typing import List

class AsyncTaskExecutor:
    async def execute_tasks_parallel(self, tasks: List[Task]) -> List[TaskResult]:
        """Executa tarefas em paralelo"""
        coroutines = [self.execute_task(task) for task in tasks]
        return await asyncio.gather(*coroutines)
    
    async def execute_tasks_sequential(self, tasks: List[Task]) -> List[TaskResult]:
        """Executa tarefas sequencialmente"""
        results = []
        for task in tasks:
            result = await self.execute_task(task)
            results.append(result)
        return results
```

### 2. Caching
```python
from functools import lru_cache
import hashlib
import json

class CacheManager:
    def __init__(self):
        self.cache = {}
    
    def get_cache_key(self, operation: str, data: Dict[str, Any]) -> str:
        """Gera chave de cache"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(f"{operation}:{data_str}".encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        """Obtém valor do cache"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Define valor no cache"""
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def is_valid(self, key: str) -> bool:
        """Verifica se cache é válido"""
        if key not in self.cache:
            return False
        return time.time() < self.cache[key]['expires_at']
```

## 📋 Conclusão

A arquitetura técnica do **Agent Orchestrator** foi projetada seguindo os princípios de:

1. **Clean Architecture**: Separação clara de responsabilidades
2. **SOLID Principles**: Código modular e extensível
3. **Async/Await**: Performance otimizada
4. **Structured Logging**: Observabilidade completa
5. **Comprehensive Testing**: Qualidade garantida
6. **Security First**: Validação e sanitização robustas

Esta arquitetura permite:
- **Escalabilidade**: Suporte a múltiplos projetos
- **Manutenibilidade**: Código limpo e bem estruturado
- **Extensibilidade**: Fácil adição de novos agentes
- **Confiabilidade**: Tratamento robusto de erros
- **Performance**: Otimizações assíncronas e cache 