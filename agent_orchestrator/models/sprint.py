"""
Sprint Models - Agent Orchestrator
Modelos de dados para sprints
"""

from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, validator

from .backlog import UserStory


class Sprint(BaseModel):
    """Modelo para Sprint"""
    
    id: str = Field(..., description="ID único do sprint")
    name: str = Field(..., description="Nome do sprint")
    description: str = Field(..., description="Descrição do sprint")
    user_stories: List[UserStory] = Field(default_factory=list, description="User stories do sprint")
    max_points: int = Field(..., description="Máximo de pontos do sprint")
    start_date: datetime = Field(..., description="Data de início")
    end_date: datetime = Field(..., description="Data de fim")
    status: str = Field("planned", description="Status do sprint")
    velocity: Optional[float] = Field(None, description="Velocidade do sprint")
    actual_points: Optional[int] = Field(None, description="Pontos reais completados")
    
    @validator('id')
    def validate_id(cls, v):
        """Valida formato do ID"""
        if not v.startswith('SPRINT-'):
            raise ValueError('ID deve começar com SPRINT-')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Valida status do sprint"""
        valid_statuses = ['planned', 'in_progress', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'Status deve ser um de: {valid_statuses}')
        return v
    
    @validator('max_points')
    def validate_max_points(cls, v):
        """Valida pontos máximos"""
        if v <= 0:
            raise ValueError('Pontos máximos deve ser maior que 0')
        if v > 100:
            raise ValueError('Pontos máximos deve ser menor que 100')
        return v
    
    def calculate_actual_points(self) -> int:
        """Calcula pontos reais completados"""
        if self.status == 'completed':
            self.actual_points = sum(story.story_points for story in self.user_stories)
        else:
            self.actual_points = 0
        return self.actual_points
    
    def calculate_velocity(self) -> Optional[float]:
        """Calcula velocidade do sprint"""
        if self.status == 'completed' and self.actual_points:
            duration = (self.end_date - self.start_date).days
            if duration > 0:
                self.velocity = self.actual_points / duration
                return self.velocity
        return None
    
    def get_completion_percentage(self) -> float:
        """Calcula porcentagem de conclusão"""
        if self.max_points == 0:
            return 0.0
        actual = self.actual_points or 0
        return (actual / self.max_points) * 100
    
    def is_overdue(self) -> bool:
        """Verifica se o sprint está atrasado"""
        if self.status in ['completed', 'cancelled']:
            return False
        return datetime.now() > self.end_date
    
    def get_remaining_days(self) -> int:
        """Retorna dias restantes"""
        if self.status in ['completed', 'cancelled']:
            return 0
        remaining = self.end_date - datetime.now()
        return max(0, remaining.days)
    
    def get_burndown_data(self) -> List[dict]:
        """Retorna dados para gráfico de burndown"""
        from datetime import datetime, timedelta
        
        if self.status == "planned":
            # Sprint ainda não iniciado
            return [
                {"day": 0, "remaining": self.max_points},
                {"day": 14, "remaining": self.max_points}
            ]
        
        # Calcular dados reais de burndown
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return [{"day": 0, "remaining": self.max_points}]
        
        # Calcular progresso baseado no tempo decorrido
        days_elapsed = (datetime.now() - self.start_date).days
        days_elapsed = max(0, min(days_elapsed, total_days))
        
        # Calcular pontos restantes baseado no progresso
        if self.status == "completed":
            remaining_points = 0
        elif self.actual_points is not None:
            # Usar pontos reais se disponível
            remaining_points = max(0, self.max_points - self.actual_points)
        else:
            # Estimar baseado no tempo decorrido
            progress_ratio = days_elapsed / total_days
            remaining_points = max(0, self.max_points * (1 - progress_ratio))
        
        # Gerar dados de burndown
        burndown_data = []
        for day in range(total_days + 1):
            if day <= days_elapsed:
                # Dias já passados
                if self.status == "completed":
                    day_remaining = 0
                else:
                    day_remaining = max(0, self.max_points * (1 - (day / total_days)))
            else:
                # Dias futuros (estimativa)
                day_remaining = max(0, self.max_points * (1 - (day / total_days)))
            
            burndown_data.append({
                "day": day,
                "remaining": round(day_remaining, 1),
                "actual": day <= days_elapsed
            })
        
        return burndown_data
    
    def add_user_story(self, story: UserStory) -> bool:
        """Adiciona user story ao sprint"""
        # Verificar se cabe no sprint
        current_points = sum(s.story_points for s in self.user_stories)
        if current_points + story.story_points <= self.max_points:
            self.user_stories.append(story)
            return True
        return False
    
    def remove_user_story(self, story_id: str) -> bool:
        """Remove user story do sprint"""
        for i, story in enumerate(self.user_stories):
            if story.id == story_id:
                del self.user_stories[i]
                return True
        return False
    
    def get_stories_by_priority(self, priority: str) -> List[UserStory]:
        """Retorna stories por prioridade"""
        return [story for story in self.user_stories if story.priority == priority]
    
    def get_stories_by_status(self, status: str) -> List[UserStory]:
        """Retorna stories por status"""
        # Mapear status do sprint para status das stories
        if self.status == "completed":
            # Se sprint está completo, todas as stories estão completas
            return self.user_stories if status == "completed" else []
        elif self.status == "in_progress":
            # Durante o sprint, estimar baseado no tempo decorrido
            from datetime import datetime
            total_days = (self.end_date - self.start_date).days
            days_elapsed = (datetime.now() - self.start_date).days
            
            if total_days > 0:
                progress_ratio = min(1.0, days_elapsed / total_days)
                completed_count = int(len(self.user_stories) * progress_ratio)
                
                if status == "completed":
                    return self.user_stories[:completed_count]
                elif status == "in_progress":
                    return self.user_stories[completed_count:completed_count + 1] if completed_count < len(self.user_stories) else []
                elif status == "pending":
                    return self.user_stories[completed_count + 1:]
            
            # Fallback: todas as stories estão em progresso
            return self.user_stories if status == "in_progress" else []
        else:
            # Sprint planejado, todas as stories estão pendentes
            return self.user_stories if status == "pending" else []
    
    def validate_dependencies(self) -> bool:
        """Valida dependências entre stories"""
        story_ids = {story.id for story in self.user_stories}
        
        for story in self.user_stories:
            for dep_id in story.dependencies:
                if dep_id not in story_ids:
                    raise ValueError(f"Dependência {dep_id} não satisfeita para {story.id}")
        return True 