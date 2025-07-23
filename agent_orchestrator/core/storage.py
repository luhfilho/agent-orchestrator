"""
Storage System - Agent Orchestrator
Sistema de persistência para sprints e dados
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from ..models.sprint import Sprint
from ..models.backlog import Backlog, UserStory
from ..models.task import Task, TaskResult
from ..utils.logger import logger


@dataclass
class StorageConfig:
    """Configuração do sistema de storage"""
    data_dir: Path = Path("./data")
    sprints_file: str = "sprints.json"
    backlogs_file: str = "backlogs.json"
    tasks_file: str = "tasks.json"
    results_file: str = "results.json"


class SprintStorage:
    """Sistema de persistência para sprints"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.logger = logger
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe"""
        self.config.data_dir.mkdir(exist_ok=True)
    
    async def save_sprint(self, sprint: Sprint) -> bool:
        """Salva um sprint"""
        try:
            sprints = await self.load_all_sprints()
            sprints[sprint.id] = self._sprint_to_dict(sprint)
            
            await self._save_sprints(sprints)
            self.logger.info(f"✅ Sprint {sprint.id} salvo com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar sprint {sprint.id}: {str(e)}")
            return False
    
    async def load_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Carrega um sprint pelo ID"""
        try:
            sprints = await self.load_all_sprints()
            sprint_data = sprints.get(sprint_id)
            
            if sprint_data:
                return self._dict_to_sprint(sprint_data)
            else:
                self.logger.warning(f"⚠️ Sprint {sprint_id} não encontrado")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar sprint {sprint_id}: {str(e)}")
            return None
    
    async def load_all_sprints(self) -> Dict[str, Dict[str, Any]]:
        """Carrega todos os sprints"""
        sprints_file = self.config.data_dir / self.config.sprints_file
        
        if not sprints_file.exists():
            return {}
        
        try:
            async with asyncio.Lock():
                with open(sprints_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar sprints: {str(e)}")
            return {}
    
    async def delete_sprint(self, sprint_id: str) -> bool:
        """Deleta um sprint"""
        try:
            sprints = await self.load_all_sprints()
            
            if sprint_id in sprints:
                del sprints[sprint_id]
                await self._save_sprints(sprints)
                self.logger.info(f"✅ Sprint {sprint_id} deletado com sucesso")
                return True
            else:
                self.logger.warning(f"⚠️ Sprint {sprint_id} não encontrado para deletar")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao deletar sprint {sprint_id}: {str(e)}")
            return False
    
    async def list_sprints(self) -> List[Sprint]:
        """Lista todos os sprints"""
        try:
            sprints_data = await self.load_all_sprints()
            sprints = []
            
            for sprint_data in sprints_data.values():
                sprint = self._dict_to_sprint(sprint_data)
                sprints.append(sprint)
            
            return sprints
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar sprints: {str(e)}")
            return []
    
    async def _save_sprints(self, sprints: Dict[str, Dict[str, Any]]):
        """Salva sprints no arquivo"""
        sprints_file = self.config.data_dir / self.config.sprints_file
        
        async with asyncio.Lock():
            with open(sprints_file, 'w', encoding='utf-8') as f:
                json.dump(sprints, f, indent=2, ensure_ascii=False, default=str)
    
    def _sprint_to_dict(self, sprint: Sprint) -> Dict[str, Any]:
        """Converte sprint para dicionário"""
        return {
            "id": sprint.id,
            "name": sprint.name,
            "description": sprint.description,
            "max_points": sprint.max_points,
            "start_date": sprint.start_date.isoformat(),
            "end_date": sprint.end_date.isoformat(),
            "status": sprint.status,
            "velocity": sprint.velocity,
            "actual_points": sprint.actual_points,
            "user_stories": [
                {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "acceptance_criteria": story.acceptance_criteria,
                    "story_points": story.story_points,
                    "priority": story.priority,
                    "dependencies": story.dependencies
                }
                for story in sprint.user_stories
            ]
        }
    
    def _dict_to_sprint(self, data: Dict[str, Any]) -> Sprint:
        """Converte dicionário para sprint"""
        from ..models.backlog import UserStory
        
        # Converter user stories
        user_stories = []
        for story_data in data.get("user_stories", []):
            story = UserStory(
                id=story_data["id"],
                title=story_data["title"],
                description=story_data["description"],
                acceptance_criteria=story_data["acceptance_criteria"],
                story_points=story_data["story_points"],
                priority=story_data["priority"],
                dependencies=story_data.get("dependencies", [])
            )
            user_stories.append(story)
        
        # Converter datas
        start_date = datetime.fromisoformat(data["start_date"])
        end_date = datetime.fromisoformat(data["end_date"])
        
        return Sprint(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            user_stories=user_stories,
            max_points=data["max_points"],
            start_date=start_date,
            end_date=end_date,
            status=data["status"],
            velocity=data.get("velocity"),
            actual_points=data.get("actual_points")
        )


class TaskStorage:
    """Sistema de persistência para tasks"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.logger = logger
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Garante que o diretório de dados existe"""
        self.config.data_dir.mkdir(exist_ok=True)
    
    async def save_task_result(self, task_id: str, result: TaskResult) -> bool:
        """Salva resultado de uma task"""
        try:
            results = await self.load_all_task_results()
            results[task_id] = self._task_result_to_dict(result)
            
            await self._save_task_results(results)
            self.logger.info(f"✅ Resultado da task {task_id} salvo com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar resultado da task {task_id}: {str(e)}")
            return False
    
    async def load_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Carrega resultado de uma task"""
        try:
            results = await self.load_all_task_results()
            result_data = results.get(task_id)
            
            if result_data:
                return self._dict_to_task_result(result_data)
            else:
                self.logger.warning(f"⚠️ Resultado da task {task_id} não encontrado")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar resultado da task {task_id}: {str(e)}")
            return None
    
    async def load_all_task_results(self) -> Dict[str, Dict[str, Any]]:
        """Carrega todos os resultados de tasks"""
        results_file = self.config.data_dir / self.config.results_file
        
        if not results_file.exists():
            return {}
        
        try:
            async with asyncio.Lock():
                with open(results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar resultados: {str(e)}")
            return {}
    
    async def _save_task_results(self, results: Dict[str, Dict[str, Any]]):
        """Salva resultados no arquivo"""
        results_file = self.config.data_dir / self.config.results_file
        
        async with asyncio.Lock():
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    def _task_result_to_dict(self, result: TaskResult) -> Dict[str, Any]:
        """Converte TaskResult para dicionário"""
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "error": result.error,
            "execution_time": result.execution_time,
            "agent_used": result.agent_used,
            "timestamp": datetime.now().isoformat()
        }
    
    def _dict_to_task_result(self, data: Dict[str, Any]) -> TaskResult:
        """Converte dicionário para TaskResult"""
        return TaskResult(
            success=data["success"],
            message=data["message"],
            data=data.get("data"),
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
            agent_used=data.get("agent_used", "unknown")
        )


class StorageManager:
    """Gerenciador central de storage"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.sprint_storage = SprintStorage(config)
        self.task_storage = TaskStorage(config)
        self.logger = logger
    
    async def save_sprint(self, sprint: Sprint) -> bool:
        """Salva um sprint"""
        return await self.sprint_storage.save_sprint(sprint)
    
    async def load_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Carrega um sprint"""
        return await self.sprint_storage.load_sprint(sprint_id)
    
    async def list_sprints(self) -> List[Sprint]:
        """Lista todos os sprints"""
        return await self.sprint_storage.list_sprints()
    
    async def delete_sprint(self, sprint_id: str) -> bool:
        """Deleta um sprint"""
        return await self.sprint_storage.delete_sprint(sprint_id)
    
    async def save_task_result(self, task_id: str, result: TaskResult) -> bool:
        """Salva resultado de uma task"""
        return await self.task_storage.save_task_result(task_id, result)
    
    async def load_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Carrega resultado de uma task"""
        return await self.task_storage.load_task_result(task_id)
    
    async def get_sprint_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos sprints"""
        sprints = await self.list_sprints()
        
        if not sprints:
            return {
                "total_sprints": 0,
                "completed_sprints": 0,
                "in_progress_sprints": 0,
                "planned_sprints": 0,
                "total_points": 0,
                "average_velocity": 0.0
            }
        
        completed = len([s for s in sprints if s.status == "completed"])
        in_progress = len([s for s in sprints if s.status == "in_progress"])
        planned = len([s for s in sprints if s.status == "planned"])
        total_points = sum(s.max_points for s in sprints)
        
        velocities = [s.velocity for s in sprints if s.velocity is not None]
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0.0
        
        return {
            "total_sprints": len(sprints),
            "completed_sprints": completed,
            "in_progress_sprints": in_progress,
            "planned_sprints": planned,
            "total_points": total_points,
            "average_velocity": avg_velocity
        } 