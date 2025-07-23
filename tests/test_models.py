"""
Test Models - Agent Orchestrator
Testes unitários para modelos de dados
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from agent_orchestrator.models.backlog import Backlog, UserStory
from agent_orchestrator.models.task import Task, TaskResult


class TestUserStory:
    """Testes para modelo UserStory"""
    
    def test_valid_user_story(self):
        """Testa criação de user story válida"""
        story = UserStory(
            id="US-001",
            title="Implementar login",
            description="Sistema de autenticação de usuários",
            acceptance_criteria=["Usuário pode fazer login", "Validação de credenciais"],
            story_points=5,
            priority="P0"
        )
        
        assert story.id == "US-001"
        assert story.title == "Implementar login"
        assert story.story_points == 5
        assert story.priority == "P0"
    
    def test_invalid_id_format(self):
        """Testa validação de formato de ID"""
        with pytest.raises(ValidationError, match="ID deve seguir o padrão US-XXX"):
            UserStory(
                id="INVALID-001",
                title="Test",
                description="Test",
                story_points=5,
                priority="P0"
            )
    
    def test_invalid_priority(self):
        """Testa validação de prioridade"""
        with pytest.raises(ValidationError, match="Prioridade deve ser uma de"):
            UserStory(
                id="US-001",
                title="Test",
                description="Test",
                story_points=5,
                priority="INVALID"
            )
    
    def test_invalid_story_points(self):
        """Testa validação de story points (Fibonacci)"""
        with pytest.raises(ValidationError, match="Story points deve ser um número Fibonacci"):
            UserStory(
                id="US-001",
                title="Test",
                description="Test",
                story_points=4,  # Não é Fibonacci
                priority="P0"
            )


class TestBacklog:
    """Testes para modelo Backlog"""
    
    def test_valid_backlog(self):
        """Testa criação de backlog válido"""
        stories = [
            UserStory(
                id="US-001",
                title="Story 1",
                description="Description 1",
                story_points=5,
                priority="P0"
            ),
            UserStory(
                id="US-002",
                title="Story 2",
                description="Description 2",
                story_points=8,
                priority="P1"
            )
        ]
        
        backlog = Backlog(
            id="BL-001",
            title="Backlog Principal",
            description="Backlog do projeto",
            user_stories=stories
        )
        
        assert backlog.id == "BL-001"
        assert len(backlog.user_stories) == 2
        assert backlog.calculate_total_points() == 13
    
    def test_invalid_backlog_id(self):
        """Testa validação de ID do backlog"""
        with pytest.raises(ValidationError, match="ID deve seguir o padrão BL-XXX"):
            Backlog(
                id="INVALID-001",
                title="Test",
                description="Test",
                user_stories=[]
            )
    
    def test_get_stories_by_priority(self):
        """Testa filtro de stories por prioridade"""
        stories = [
            UserStory(id="US-001", title="P0 Story", description="", story_points=5, priority="P0"),
            UserStory(id="US-002", title="P1 Story", description="", story_points=8, priority="P1"),
            UserStory(id="US-003", title="P0 Story 2", description="", story_points=3, priority="P0")
        ]
        
        backlog = Backlog(
            id="BL-001",
            title="Test",
            description="Test",
            user_stories=stories
        )
        
        p0_stories = backlog.get_stories_by_priority("P0")
        assert len(p0_stories) == 2
        assert all(story.priority == "P0" for story in p0_stories)
    
    def test_get_stories_by_points(self):
        """Testa seleção de stories por limite de pontos"""
        stories = [
            UserStory(id="US-001", title="Story 1", description="", story_points=5, priority="P0"),
            UserStory(id="US-002", title="Story 2", description="", story_points=8, priority="P1"),
            UserStory(id="US-003", title="Story 3", description="", story_points=13, priority="P2")
        ]
        
        backlog = Backlog(
            id="BL-001",
            title="Test",
            description="Test",
            user_stories=stories
        )
        
        selected = backlog.get_stories_by_points(15)
        assert len(selected) == 2  # Deve pegar as 2 primeiras (5 + 8 = 13)
        assert sum(story.story_points for story in selected) == 13


class TestTask:
    """Testes para modelo Task"""
    
    def test_valid_task(self):
        """Testa criação de task válida"""
        task = Task(
            id="TASK-001",
            title="Implementar feature",
            description="Implementar nova funcionalidade",
            user_story_id="US-001",
            agent_type="claude"
        )
        
        assert task.id == "TASK-001"
        assert task.status == "pending"
        assert task.agent_type == "claude"
    
    def test_invalid_task_id(self):
        """Testa validação de ID da task"""
        with pytest.raises(ValidationError, match="ID deve seguir o padrão TASK-XXX"):
            Task(
                id="INVALID-001",
                title="Test",
                description="Test",
                user_story_id="US-001",
                agent_type="claude"
            )
    
    def test_invalid_agent_type(self):
        """Testa validação de tipo de agente"""
        with pytest.raises(ValidationError, match="Tipo de agente deve ser um de"):
            Task(
                id="TASK-001",
                title="Test",
                description="Test",
                user_story_id="US-001",
                agent_type="invalid"
            )
    
    def test_task_execution_lifecycle(self):
        """Testa ciclo de vida da task"""
        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test Description",
            user_story_id="US-001",
            agent_type="claude"
        )
        
        # Inicialmente pendente
        assert task.is_pending()
        assert not task.is_running()
        assert not task.is_completed()
        
        # Iniciar execução
        task.start_execution()
        assert task.is_running()
        assert task.started_at is not None
        
        # Completar com sucesso
        result = TaskResult(
            success=True,
            message="Task completed successfully",
            execution_time=5.2,
            agent_used="claude"
        )
        task.complete_execution(result)
        
        assert task.is_completed()
        assert task.status == "completed"
        assert task.result == result
        assert task.completed_at is not None
    
    def test_task_failure(self):
        """Testa falha na execução da task"""
        task = Task(
            id="TASK-001",
            title="Test Task",
            description="Test Description",
            user_story_id="US-001",
            agent_type="claude"
        )
        
        task.start_execution()
        task.fail_execution("API timeout")
        
        assert task.status == "failed"
        assert task.error == "API timeout"
        assert task.completed_at is not None


class TestTaskResult:
    """Testes para modelo TaskResult"""
    
    def test_successful_result(self):
        """Testa resultado de sucesso"""
        result = TaskResult(
            success=True,
            message="Task completed successfully",
            data={"files_created": 3, "tests_passed": True},
            execution_time=5.2,
            agent_used="claude"
        )
        
        assert result.success is True
        assert result.message == "Task completed successfully"
        assert result.data["files_created"] == 3
        assert result.execution_time == 5.2
        assert result.agent_used == "claude"
    
    def test_failed_result(self):
        """Testa resultado de falha"""
        result = TaskResult(
            success=False,
            message="Task failed",
            error="API connection timeout",
            execution_time=2.1,
            agent_used="gemini"
        )
        
        assert result.success is False
        assert result.error == "API connection timeout"
        assert result.execution_time == 2.1
        assert result.agent_used == "gemini" 