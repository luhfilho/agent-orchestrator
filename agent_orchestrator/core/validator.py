"""
Task Validator - Agent Orchestrator
Validador para tasks e backlogs
"""

import re
from typing import List, Dict, Any
from pathlib import Path

from ..models.backlog import Backlog, UserStory
from ..models.task import Task
from ..utils.logger import logger


class TaskValidator:
    """Validador para tasks e backlogs"""
    
    def __init__(self):
        self.logger = logger
    
    def validate_backlog(self, backlog: Backlog) -> bool:
        """
        Valida um backlog
        
        Args:
            backlog: Backlog a ser validado
            
        Returns:
            bool: True se válido
            
        Raises:
            ValueError: Se backlog inválido
        """
        self.logger.info(f"🔍 Validando backlog: {backlog.id}")
        
        # Validar ID
        if not re.match(r'^BL-\d+$', backlog.id):
            raise ValueError(f"ID de backlog inválido: {backlog.id}")
        
        # Validar título
        if not backlog.title or len(backlog.title.strip()) == 0:
            raise ValueError("Título do backlog não pode ser vazio")
        
        # Validar user stories
        if not backlog.user_stories:
            raise ValueError("Backlog deve ter pelo menos uma user story")
        
        # Validar cada user story
        for story in backlog.user_stories:
            self._validate_user_story(story)
        
        # Validar dependências
        self._validate_backlog_dependencies(backlog)
        
        self.logger.success(f"✅ Backlog {backlog.id} validado com sucesso")
        return True
    
    def validate_task(self, task: Task) -> bool:
        """
        Valida uma task
        
        Args:
            task: Task a ser validada
            
        Returns:
            bool: True se válida
            
        Raises:
            ValueError: Se task inválida
        """
        self.logger.info(f"🔍 Validando task: {task.id}")
        
        # Validar ID
        if not re.match(r'^TASK-\d+$', task.id):
            raise ValueError(f"ID de task inválido: {task.id}")
        
        # Validar título
        if not task.title or len(task.title.strip()) == 0:
            raise ValueError("Título da task não pode ser vazio")
        
        # Validar descrição
        if not task.description or len(task.description.strip()) == 0:
            raise ValueError("Descrição da task não pode ser vazia")
        
        # Validar user story ID
        if not re.match(r'^US-\d+$', task.user_story_id):
            raise ValueError(f"ID de user story inválido: {task.user_story_id}")
        
        # Validar agente
        valid_agents = ['claude', 'gemini', 'auto']
        if task.agent_type not in valid_agents:
            raise ValueError(f"Tipo de agente inválido: {task.agent_type}")
        
        # Validar prioridade
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if task.priority not in valid_priorities:
            raise ValueError(f"Prioridade inválida: {task.priority}")
        
        # Validar complexidade
        valid_complexities = ['low', 'medium', 'high']
        if task.complexity not in valid_complexities:
            raise ValueError(f"Complexidade inválida: {task.complexity}")
        
        self.logger.success(f"✅ Task {task.id} validada com sucesso")
        return True
    
    def validate_sprint(self, sprint) -> bool:
        """
        Valida um sprint
        
        Args:
            sprint: Sprint a ser validado
            
        Returns:
            bool: True se válido
        """
        self.logger.info(f"🔍 Validando sprint: {sprint.id}")
        
        # Validar ID
        if not sprint.id.startswith('SPRINT-'):
            raise ValueError(f"ID de sprint inválido: {sprint.id}")
        
        # Validar pontos máximos
        if sprint.max_points <= 0:
            raise ValueError("Pontos máximos deve ser maior que 0")
        
        # Validar datas
        if sprint.start_date >= sprint.end_date:
            raise ValueError("Data de início deve ser anterior à data de fim")
        
        # Validar user stories
        if not sprint.user_stories:
            raise ValueError("Sprint deve ter pelo menos uma user story")
        
        # Validar pontos das stories
        total_points = sum(story.story_points for story in sprint.user_stories)
        if total_points > sprint.max_points:
            raise ValueError(f"Total de pontos ({total_points}) excede o máximo ({sprint.max_points})")
        
        # Validar dependências
        self._validate_sprint_dependencies(sprint)
        
        self.logger.success(f"✅ Sprint {sprint.id} validado com sucesso")
        return True
    
    def validate_file_path(self, file_path: Path) -> bool:
        """
        Valida um caminho de arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se válido
        """
        # Validar se arquivo existe
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        # Validar extensão
        valid_extensions = ['.md', '.txt', '.json', '.yaml', '.yml']
        if file_path.suffix.lower() not in valid_extensions:
            raise ValueError(f"Extensão de arquivo não suportada: {file_path.suffix}")
        
        # Validar tamanho (máximo 10MB)
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise ValueError(f"Arquivo muito grande: {file_size} bytes (máximo: {max_size})")
        
        return True
    
    def _validate_user_story(self, story: UserStory) -> None:
        """Valida uma user story individual"""
        # Validar ID
        if not re.match(r'^US-\d+$', story.id):
            raise ValueError(f"ID de user story inválido: {story.id}")
        
        # Validar título
        if not story.title or len(story.title.strip()) == 0:
            raise ValueError(f"Título da user story {story.id} não pode ser vazio")
        
        # Validar descrição
        if not story.description or len(story.description.strip()) == 0:
            raise ValueError(f"Descrição da user story {story.id} não pode ser vazia")
        
        # Validar story points
        if story.story_points <= 0:
            raise ValueError(f"Story points da user story {story.id} deve ser maior que 0")
        
        # Validar prioridade
        valid_priorities = ['P0', 'P1', 'P2', 'P3']
        if story.priority not in valid_priorities:
            raise ValueError(f"Prioridade inválida na user story {story.id}: {story.priority}")
    
    def _validate_backlog_dependencies(self, backlog: Backlog) -> None:
        """Valida dependências do backlog"""
        story_ids = {story.id for story in backlog.user_stories}
        
        for story in backlog.user_stories:
            for dep_id in story.dependencies:
                if dep_id not in story_ids:
                    raise ValueError(f"Dependência {dep_id} não encontrada para user story {story.id}")
    
    def _validate_sprint_dependencies(self, sprint) -> None:
        """Valida dependências do sprint"""
        story_ids = {story.id for story in sprint.user_stories}
        
        for story in sprint.user_stories:
            for dep_id in story.dependencies:
                if dep_id not in story_ids:
                    raise ValueError(f"Dependência {dep_id} não satisfeita no sprint para {story.id}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida configuração do sistema
        
        Args:
            config: Configuração a ser validada
            
        Returns:
            bool: True se válida
        """
        required_keys = ['claude_api_key', 'gemini_api_key', 'log_level']
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Configuração obrigatória ausente: {key}")
        
        # Validar API keys
        if not config['claude_api_key'] or config['claude_api_key'] == 'YOUR_KEY':
            raise ValueError("Claude API key não configurada")
        
        if not config['gemini_api_key'] or config['gemini_api_key'] == 'YOUR_KEY':
            raise ValueError("Gemini API key não configurada")
        
        # Validar log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        if config['log_level'] not in valid_log_levels:
            raise ValueError(f"Log level inválido: {config['log_level']}")
        
        return True 