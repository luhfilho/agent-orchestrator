"""
Backlog Models - Agent Orchestrator
Modelos de dados para backlog e user stories
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import re


class UserStory(BaseModel):
    """Modelo para User Story"""
    
    id: str = Field(..., description="ID único da user story")
    title: str = Field(..., description="Título da user story")
    description: str = Field(..., description="Descrição detalhada")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Critérios de aceite")
    story_points: int = Field(..., ge=1, le=21, description="Pontos da story (Fibonacci)")
    priority: str = Field(..., description="Prioridade (P0, P1, P2, P3)")
    dependencies: List[str] = Field(default_factory=list, description="IDs das dependências")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data de atualização")
    
    @validator('id')
    def validate_id(cls, v):
        """Valida formato do ID"""
        if not re.match(r'^US-\d+$', v):
            raise ValueError('ID deve seguir o padrão US-XXX')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        """Valida prioridade"""
        valid_priorities = ['P0', 'P1', 'P2', 'P3']
        if v not in valid_priorities:
            raise ValueError(f'Prioridade deve ser uma de: {valid_priorities}')
        return v
    
    @validator('story_points')
    def validate_story_points(cls, v):
        """Valida story points (Fibonacci)"""
        fibonacci = [1, 2, 3, 5, 8, 13, 21]
        if v not in fibonacci:
            raise ValueError(f'Story points deve ser um número Fibonacci: {fibonacci}')
        return v


class Backlog(BaseModel):
    """Modelo para Backlog"""
    
    id: str = Field(..., description="ID único do backlog")
    title: str = Field(..., description="Título do backlog")
    description: str = Field(..., description="Descrição do backlog")
    user_stories: List[UserStory] = Field(default_factory=list, description="Lista de user stories")
    total_points: int = Field(0, description="Total de pontos do backlog")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data de atualização")
    
    @validator('id')
    def validate_id(cls, v):
        """Valida formato do ID"""
        if not re.match(r'^BL-\d+$', v):
            raise ValueError('ID deve seguir o padrão BL-XXX')
        return v
    
    def calculate_total_points(self) -> int:
        """Calcula total de pontos do backlog"""
        self.total_points = sum(story.story_points for story in self.user_stories)
        return self.total_points
    
    def get_stories_by_priority(self, priority: str) -> List[UserStory]:
        """Retorna stories por prioridade"""
        return [story for story in self.user_stories if story.priority == priority]
    
    def get_stories_by_points(self, max_points: int) -> List[UserStory]:
        """Retorna stories que cabem em um limite de pontos"""
        stories = []
        current_points = 0
        
        for story in sorted(self.user_stories, key=lambda x: x.priority):
            if current_points + story.story_points <= max_points:
                stories.append(story)
                current_points += story.story_points
        
        return stories
    
    def validate_dependencies(self) -> bool:
        """Valida se todas as dependências existem"""
        story_ids = {story.id for story in self.user_stories}
        
        for story in self.user_stories:
            for dep_id in story.dependencies:
                if dep_id not in story_ids:
                    raise ValueError(f'Dependência {dep_id} não encontrada para story {story.id}')
        
        return True 