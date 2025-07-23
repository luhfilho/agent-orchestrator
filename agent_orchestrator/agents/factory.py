"""
Agent Factory - Agent Orchestrator
Factory para criação e gerenciamento de agentes
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .claude_agent import ClaudeAgent, ClaudeConfig
from .gemini_agent import GeminiAgent, GeminiConfig
from ..models.task import Task, TaskResult
from ..utils.logger import logger


class AgentType(Enum):
    """Tipos de agentes disponíveis"""
    CLAUDE = "claude"
    GEMINI = "gemini"
    AUTO = "auto"


@dataclass
class AgentCapabilities:
    """Capacidades de um agente"""
    name: str
    type: str
    complexity_threshold: int
    execution_speed: str  # "fast", "medium", "slow"
    cost_per_token: float
    max_tokens: int
    personas: List[str] = None
    mcp_servers: List[str] = None


class AgentFactory:
    """Factory para criação e gerenciamento de agentes"""
    
    def __init__(self):
        self.logger = logger
        self._agents: Dict[str, Any] = {}
        self._capabilities = self._define_capabilities()
        self._agent_stats: Dict[str, Dict[str, Any]] = {}
    
    def _define_capabilities(self) -> Dict[str, AgentCapabilities]:
        """Define capacidades de cada agente"""
        return {
            AgentType.CLAUDE.value: AgentCapabilities(
                name="Claude Code",
                type="complex_tasks",
                complexity_threshold=8,  # Pontos para considerar tarefa complexa
                execution_speed="slow",
                cost_per_token=0.000015,  # Custo por token (aproximado)
                max_tokens=4000,
                personas=["sm", "dev", "qa", "pm", "po"]
            ),
            AgentType.GEMINI.value: AgentCapabilities(
                name="Gemini CLI",
                type="fast_tasks",
                complexity_threshold=5,
                execution_speed="fast",
                cost_per_token=0.000007,  # Custo por token (aproximado)
                max_tokens=2000,
                mcp_servers=["filesystem", "git", "github", "terminal"]
            )
        }
    
    def get_agent(self, agent_type: str, config_overrides: Optional[Dict[str, Any]] = None) -> Any:
        """
        Obtém um agente pelo tipo
        
        Args:
            agent_type: Tipo do agente (claude, gemini, auto)
            config_overrides: Overrides de configuração para o agente
            
        Returns:
            Agente configurado
        """
        if agent_type == AgentType.AUTO.value:
            # Auto seleciona baseado na task
            return self._get_auto_agent()
        
        agent_key = f"{agent_type}_{hash(str(config_overrides))}" if config_overrides else agent_type
        
        if agent_key not in self._agents:
            self._agents[agent_key] = self._create_agent(agent_type, config_overrides)
        
        return self._agents[agent_key]
    
    def _create_agent(self, agent_type: str, config_overrides: Optional[Dict[str, Any]] = None) -> Any:
        """Cria um agente específico"""
        try:
            if agent_type == AgentType.CLAUDE.value:
                config = ClaudeConfig()
                if config_overrides:
                    for key, value in config_overrides.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                return ClaudeAgent(config)
            elif agent_type == AgentType.GEMINI.value:
                config = GeminiConfig()
                if config_overrides:
                    for key, value in config_overrides.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                return GeminiAgent(config)
            else:
                raise ValueError(f"Tipo de agente não suportado: {agent_type}")
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar agente {agent_type}: {str(e)}")
            raise
    
    def _get_auto_agent(self) -> Any:
        """Retorna agente para seleção automática"""
        # Por enquanto, retorna um wrapper que seleciona automaticamente
        return AutoAgent(self)
    
    def select_agent_for_task(self, task: Task) -> str:
        """
        Seleciona o melhor agente para uma task
        
        Args:
            task: Task a ser executada
            
        Returns:
            Tipo do agente selecionado
        """
        # Análise da complexidade da task
        complexity_score = self._calculate_task_complexity(task)
        
        # Análise do tipo de task
        task_type = self._analyze_task_type(task)
        
        # Seleção baseada em critérios
        if complexity_score >= self._capabilities[AgentType.CLAUDE.value].complexity_threshold:
            return AgentType.CLAUDE.value
        elif task_type in ["test", "qa", "quality"]:
            return AgentType.CLAUDE.value  # Claude tem personas especializadas
        elif task_type in ["quick", "simple", "prototype"]:
            return AgentType.GEMINI.value
        else:
            # Padrão: Claude para todas as tarefas
            return AgentType.CLAUDE.value
    
    def _calculate_task_complexity(self, task: Task) -> int:
        """Calcula complexidade da task"""
        complexity = 0
        
        # Baseado nos story points
        if hasattr(task, 'story_points'):
            complexity += task.story_points
        
        # Baseado na prioridade
        priority_map = {"P0": 3, "P1": 2, "P2": 1, "P3": 0}
        complexity += priority_map.get(task.priority, 1)
        
        # Baseado na descrição
        description = task.description.lower()
        complexity_indicators = [
            "complex", "difficult", "challenging", "advanced",
            "architecture", "design", "planning", "analysis"
        ]
        
        for indicator in complexity_indicators:
            if indicator in description:
                complexity += 2
        
        return complexity
    
    def _analyze_task_type(self, task: Task) -> str:
        """Analisa o tipo da task"""
        title = task.title.lower()
        description = task.description.lower()
        
        # Padrões para diferentes tipos
        if any(word in title for word in ["test", "qa", "quality"]):
            return "test"
        elif any(word in title for word in ["quick", "simple", "fast"]):
            return "quick"
        elif any(word in title for word in ["prototype", "demo", "mock"]):
            return "prototype"
        elif any(word in title for word in ["plan", "design", "architecture"]):
            return "planning"
        else:
            return "standard"
    
    def get_agent_capabilities(self, agent_type: str) -> Optional[AgentCapabilities]:
        """Retorna capacidades de um agente"""
        return self._capabilities.get(agent_type)
    
    def get_all_capabilities(self) -> Dict[str, AgentCapabilities]:
        """Retorna capacidades de todos os agentes"""
        return self._capabilities
    
    def update_agent_stats(self, agent_type: str, stats: Dict[str, Any]):
        """Atualiza estatísticas de um agente"""
        if agent_type not in self._agent_stats:
            self._agent_stats[agent_type] = {}
        
        self._agent_stats[agent_type].update(stats)
    
    def get_agent_stats(self, agent_type: str) -> Dict[str, Any]:
        """Retorna estatísticas de um agente"""
        return self._agent_stats.get(agent_type, {})
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Retorna estatísticas de todos os agentes"""
        return self._agent_stats
    
    def configure_claude_skip_permissions(self, skip_permissions: bool = True):
        """Configura skip permissions para Claude"""
        self.logger.info(f"🔧 Configurando Claude skip_permissions: {skip_permissions}")
        # Limpar cache de agentes Claude para forçar recriação
        keys_to_remove = [k for k in self._agents.keys() if k.startswith("claude")]
        for key in keys_to_remove:
            del self._agents[key]
    
    def configure_gemini_yolo_mode(self, yolo_mode: bool = True):
        """Configura yolo mode para Gemini"""
        self.logger.info(f"🔧 Configurando Gemini yolo_mode: {yolo_mode}")
        # Limpar cache de agentes Gemini para forçar recriação
        keys_to_remove = [k for k in self._agents.keys() if k.startswith("gemini")]
        for key in keys_to_remove:
            del self._agents[key]
    
    def get_agent_with_config(self, agent_type: str, skip_permissions: bool = True, yolo_mode: bool = True) -> Any:
        """
        Obtém agente com configurações específicas
        
        Args:
            agent_type: Tipo do agente (claude, gemini, auto)
            skip_permissions: Ativar skip permissions para Claude
            yolo_mode: Ativar yolo mode para Gemini
            
        Returns:
            Agente configurado
        """
        config_overrides = {}
        
        if agent_type == AgentType.CLAUDE.value:
            config_overrides["skip_permissions"] = skip_permissions
        elif agent_type == AgentType.GEMINI.value:
            config_overrides["yolo_mode"] = yolo_mode
        
        return self.get_agent(agent_type, config_overrides)


class AutoAgent:
    """Agente que seleciona automaticamente o melhor agente para cada task"""
    
    def __init__(self, factory: AgentFactory):
        self.factory = factory
        self.logger = logger
    
    async def execute_task(self, task: Task, context: Dict[str, Any] = None) -> TaskResult:
        """
        Executa task selecionando automaticamente o melhor agente
        
        Args:
            task: Task a ser executada
            context: Contexto adicional
            
        Returns:
            TaskResult: Resultado da execução
        """
        # Selecionar agente
        agent_type = self.factory.select_agent_for_task(task)
        agent = self.factory.get_agent(agent_type)
        
        self.logger.info(f"🤖 Auto selecionou agente: {agent_type} para task {task.id}")
        
        # Executar com o agente selecionado
        result = await agent.execute_task(task, context)
        
        # Atualizar estatísticas
        self.factory.update_agent_stats(agent_type, {
            "last_used": result.execution_time,
            "success_count": 1 if result.success else 0,
            "total_count": 1
        })
        
        return result
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades do agente auto"""
        return {
            "name": "Auto Agent",
            "type": "intelligent_selection",
            "available_agents": list(self.factory._capabilities.keys()),
            "selection_criteria": [
                "task_complexity",
                "task_type", 
                "execution_speed",
                "cost_efficiency"
            ]
        } 