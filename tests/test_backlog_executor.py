"""
Testes para Backlog Executor
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from pathlib import Path

from agent_orchestrator.core.backlog_executor import (
    BacklogExecutor, BacklogExecutionStatus, BacklogExecutionState
)
from agent_orchestrator.models.backlog import Backlog, UserStory, Epic
from agent_orchestrator.models.sprint import Sprint
from agent_orchestrator.core.orchestrator import Orchestrator


class TestBacklogExecutionState:
    """Testes para BacklogExecutionState"""
    
    def test_backlog_execution_state_creation(self):
        """Testa criação de estado de execução"""
        state = BacklogExecutionState(
            backlog_id="TEST-001",
            status=BacklogExecutionStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        assert state.backlog_id == "TEST-001"
        assert state.status == BacklogExecutionStatus.IN_PROGRESS
        assert state.total_sprints == 0
        assert state.completed_sprints == 0
        assert state.failed_sprints == 0
        assert state.sprint_results is not None
        assert len(state.sprint_results) == 0


class TestBacklogExecutor:
    """Testes para BacklogExecutor"""
    
    @pytest.fixture
    def mock_orchestrator(self):
        """Mock do orchestrator"""
        orchestrator = Mock(spec=Orchestrator)
        return orchestrator
    
    @pytest.fixture
    def backlog_executor(self, mock_orchestrator):
        """Instância do backlog executor"""
        return BacklogExecutor(mock_orchestrator)
    
    @pytest.fixture
    def sample_backlog(self):
        """Backlog de exemplo para testes"""
        epic1 = Epic(
            id="EPIC-001",
            title="Epic 1",
            description="Primeira epic",
            priority="high"
        )
        
        epic2 = Epic(
            id="EPIC-002", 
            title="Epic 2",
            description="Segunda epic",
            priority="medium"
        )
        
        story1 = UserStory(
            id="US-001",
            title="User Story 1",
            description="Primeira user story",
            epic=epic1,
            story_points=5,
            priority="high",
            acceptance_criteria=["Critério 1", "Critério 2"]
        )
        
        story2 = UserStory(
            id="US-002",
            title="User Story 2", 
            description="Segunda user story",
            epic=epic1,
            story_points=8,
            priority="medium",
            acceptance_criteria=["Critério 3"]
        )
        
        story3 = UserStory(
            id="US-003",
            title="User Story 3",
            description="Terceira user story", 
            epic=epic2,
            story_points=3,
            priority="low",
            acceptance_criteria=["Critério 4", "Critério 5"]
        )
        
        return Backlog(
            id="BL-001",
            title="Backlog de Teste",
            description="Backlog para testes",
            epics=[epic1, epic2],
            user_stories=[story1, story2, story3]
        )
    
    def test_backlog_executor_initialization(self, backlog_executor):
        """Testa inicialização do backlog executor"""
        assert backlog_executor.orchestrator is not None
        assert backlog_executor.sprint_executor is not None
        assert backlog_executor.logger is not None
        assert backlog_executor.reporter is not None
        assert backlog_executor.execution_states == {}
    
    @pytest.mark.asyncio
    async def test_organize_backlog_into_sprints(self, backlog_executor, sample_backlog):
        """Testa organização do backlog em sprints"""
        sprints = await backlog_executor._organize_backlog_into_sprints(sample_backlog, 10)
        
        assert len(sprints) > 0
        assert all(isinstance(sprint, Sprint) for sprint in sprints)
        
        # Verificar se todas as stories foram distribuídas
        total_stories = sum(len(sprint.user_stories) for sprint in sprints)
        assert total_stories == len(sample_backlog.user_stories)
        
        # Verificar se pontos por sprint não excedem o limite
        for sprint in sprints:
            sprint_points = sum(story.story_points for story in sprint.user_stories)
            assert sprint_points <= 10
    
    def test_estimate_completion_time(self, backlog_executor):
        """Testa estimativa de tempo de conclusão"""
        sprints = [
            Sprint(id="SPRINT-001", name="Sprint 1", user_stories=[]),
            Sprint(id="SPRINT-002", name="Sprint 2", user_stories=[]),
            Sprint(id="SPRINT-003", name="Sprint 3", user_stories=[])
        ]
        
        estimated_time = backlog_executor._estimate_completion_time(sprints, "auto")
        
        assert isinstance(estimated_time, datetime)
        assert estimated_time > datetime.now()
    
    @pytest.mark.asyncio
    async def test_execute_backlog_success(self, backlog_executor, sample_backlog):
        """Testa execução bem-sucedida do backlog"""
        # Mock do sprint executor
        backlog_executor.sprint_executor.execute_sprint = AsyncMock(return_value=[])
        
        result = await backlog_executor.execute_backlog(
            sample_backlog,
            max_points_per_sprint=10,
            agent_type="auto",
            enable_rollback=True,
            pause_on_failure=False,
            estimate_time=True
        )
        
        assert result["backlog_id"] == sample_backlog.id
        assert result["status"] == "completed"
        assert result["total_sprints"] > 0
        assert result["completed_sprints"] > 0
        assert result["failed_sprints"] == 0
        assert "execution_time" in result
    
    @pytest.mark.asyncio
    async def test_execute_backlog_with_failure(self, backlog_executor, sample_backlog):
        """Testa execução do backlog com falha"""
        # Mock do sprint executor para simular falha
        def mock_execute_sprint(sprint, agent_type, enable_rollback, notify):
            raise Exception("Sprint execution failed")
        
        backlog_executor.sprint_executor.execute_sprint = AsyncMock(side_effect=mock_execute_sprint)
        
        result = await backlog_executor.execute_backlog(
            sample_backlog,
            max_points_per_sprint=10,
            agent_type="auto",
            enable_rollback=True,
            pause_on_failure=False,
            estimate_time=True
        )
        
        assert result["backlog_id"] == sample_backlog.id
        assert result["status"] == "failed"
        assert result["failed_sprints"] > 0
    
    def test_get_execution_status(self, backlog_executor):
        """Testa obtenção de status de execução"""
        # Criar estado de execução
        state = BacklogExecutionState(
            backlog_id="TEST-001",
            status=BacklogExecutionStatus.COMPLETED,
            start_time=datetime.now()
        )
        backlog_executor.execution_states["TEST-001"] = state
        
        # Testar obtenção
        retrieved_state = backlog_executor.get_execution_status("TEST-001")
        assert retrieved_state == state
        
        # Testar estado inexistente
        null_state = backlog_executor.get_execution_status("NONEXISTENT")
        assert null_state is None
    
    def test_get_all_execution_statuses(self, backlog_executor):
        """Testa obtenção de todos os status de execução"""
        # Criar estados de execução
        state1 = BacklogExecutionState(
            backlog_id="TEST-001",
            status=BacklogExecutionStatus.COMPLETED,
            start_time=datetime.now()
        )
        state2 = BacklogExecutionState(
            backlog_id="TEST-002",
            status=BacklogExecutionStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        backlog_executor.execution_states["TEST-001"] = state1
        backlog_executor.execution_states["TEST-002"] = state2
        
        all_states = backlog_executor.get_all_execution_statuses()
        
        assert len(all_states) == 2
        assert "TEST-001" in all_states
        assert "TEST-002" in all_states
        assert all_states["TEST-001"] == state1
        assert all_states["TEST-002"] == state2
    
    def test_pause_and_resume_execution(self, backlog_executor):
        """Testa pausar e retomar execução"""
        # Criar estado de execução em andamento
        state = BacklogExecutionState(
            backlog_id="TEST-001",
            status=BacklogExecutionStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        backlog_executor.execution_states["TEST-001"] = state
        
        # Testar pausar
        pause_result = backlog_executor.pause_backlog_execution("TEST-001")
        assert pause_result is True
        assert state.status == BacklogExecutionStatus.PAUSED
        
        # Testar retomar
        resume_result = backlog_executor.resume_backlog_execution("TEST-001")
        assert resume_result is True
        assert state.status == BacklogExecutionStatus.IN_PROGRESS
        
        # Testar com estado inexistente
        pause_result = backlog_executor.pause_backlog_execution("NONEXISTENT")
        assert pause_result is False
    
    def test_get_execution_statistics(self, backlog_executor):
        """Testa obtenção de estatísticas de execução"""
        # Criar estados de execução para teste
        completed_state = BacklogExecutionState(
            backlog_id="TEST-001",
            status=BacklogExecutionStatus.COMPLETED,
            start_time=datetime.now(),
            total_sprints=3,
            completed_sprints=3,
            failed_sprints=0
        )
        
        failed_state = BacklogExecutionState(
            backlog_id="TEST-002",
            status=BacklogExecutionStatus.FAILED,
            start_time=datetime.now(),
            total_sprints=2,
            completed_sprints=1,
            failed_sprints=1
        )
        
        paused_state = BacklogExecutionState(
            backlog_id="TEST-003",
            status=BacklogExecutionStatus.PAUSED,
            start_time=datetime.now(),
            total_sprints=1,
            completed_sprints=0,
            failed_sprints=0
        )
        
        backlog_executor.execution_states["TEST-001"] = completed_state
        backlog_executor.execution_states["TEST-002"] = failed_state
        backlog_executor.execution_states["TEST-003"] = paused_state
        
        stats = backlog_executor.get_execution_statistics()
        
        assert stats["total_executions"] == 3
        assert stats["completed_executions"] == 1
        assert stats["failed_executions"] == 1
        assert stats["paused_executions"] == 1
        assert stats["total_sprints"] == 6
        assert stats["completed_sprints"] == 4
        assert stats["failed_sprints"] == 1
        assert 0 <= stats["success_rate"] <= 100
        assert 0 <= stats["sprint_success_rate"] <= 100


if __name__ == "__main__":
    pytest.main([__file__]) 