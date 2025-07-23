"""
Integração Jira - Agent Orchestrator
Integração com Jira para sincronizar issues e sprints
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import aiohttp
from rich.console import Console
from rich.table import Table

from ..utils.advanced_logger import advanced_logger, LogLevel


@dataclass
class JiraIssue:
    """Issue do Jira"""
    key: str
    summary: str
    description: str
    status: str
    priority: str
    assignee: str
    reporter: str
    created: datetime
    updated: datetime
    labels: List[str]
    components: List[str]


@dataclass
class JiraSprint:
    """Sprint do Jira"""
    id: int
    name: str
    state: str
    start_date: datetime
    end_date: datetime
    goal: str


class JiraIntegration:
    """Integração com Jira"""
    
    def __init__(self, url: str, username: str, password: str, project_key: str):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.project_key = project_key
        self.auth = (username, password)
        self.console = Console()
        self.logger = advanced_logger
        
    async def test_connection(self) -> bool:
        """Testa conexão com Jira"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/rest/api/2/myself"
                async with session.get(url, auth=aiohttp.BasicAuth(self.username, self.password)) as response:
                    if response.status == 200:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.INFO,
                            "Conexão com Jira estabelecida",
                            data={"url": self.url, "project": self.project_key}
                        )
                        return True
                    else:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.ERROR,
                            "Falha na conexão com Jira",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return False
        except Exception as e:
            self.logger.log_error(e, {"component": "jira_integration"})
            return False
    
    async def create_issue(self, summary: str, description: str, issue_type: str = "Task",
                          priority: str = "Medium", assignee: str = None, 
                          labels: List[str] = None) -> Optional[JiraIssue]:
        """Cria issue no Jira"""
        try:
            data = {
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type},
                    "priority": {"name": priority}
                }
            }
            
            if assignee:
                data["fields"]["assignee"] = {"name": assignee}
            if labels:
                data["fields"]["labels"] = labels
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/rest/api/2/issue"
                async with session.post(url, auth=aiohttp.BasicAuth(self.username, self.password), 
                                      json=data) as response:
                    if response.status == 201:
                        issue_data = await response.json()
                        
                        # Buscar detalhes completos da issue
                        issue_key = issue_data["key"]
                        full_issue = await self.get_issue(issue_key)
                        
                        if full_issue:
                            self.logger.log_structured(
                                "jira_integration",
                                LogLevel.INFO,
                                "Issue criada com sucesso",
                                data={"issue_key": issue_key, "summary": summary}
                            )
                            
                            return full_issue
                        else:
                            return None
                    else:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.ERROR,
                            "Falha ao criar issue",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return None
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "jira_integration"})
            return None
    
    async def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Obtém issue específica do Jira"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/rest/api/2/issue/{issue_key}"
                async with session.get(url, auth=aiohttp.BasicAuth(self.username, self.password)) as response:
                    if response.status == 200:
                        issue_data = await response.json()
                        fields = issue_data["fields"]
                        
                        issue = JiraIssue(
                            key=issue_data["key"],
                            summary=fields["summary"],
                            description=fields.get("description", ""),
                            status=fields["status"]["name"],
                            priority=fields["priority"]["name"],
                            assignee=fields["assignee"]["displayName"] if fields["assignee"] else "Unassigned",
                            reporter=fields["reporter"]["displayName"],
                            created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")),
                            updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")),
                            labels=fields.get("labels", []),
                            components=[comp["name"] for comp in fields.get("components", [])]
                        )
                        
                        return issue
                    else:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.ERROR,
                            "Falha ao obter issue",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return None
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "jira_integration"})
            return None
    
    async def update_issue(self, issue_key: str, summary: str = None, description: str = None,
                          status: str = None, priority: str = None) -> Optional[JiraIssue]:
        """Atualiza issue no Jira"""
        try:
            data = {"fields": {}}
            
            if summary:
                data["fields"]["summary"] = summary
            if description:
                data["fields"]["description"] = description
            if priority:
                data["fields"]["priority"] = {"name": priority}
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/rest/api/2/issue/{issue_key}"
                async with session.put(url, auth=aiohttp.BasicAuth(self.username, self.password), 
                                     json=data) as response:
                    if response.status == 204:
                        # Buscar issue atualizada
                        updated_issue = await self.get_issue(issue_key)
                        
                        if updated_issue:
                            self.logger.log_structured(
                                "jira_integration",
                                LogLevel.INFO,
                                "Issue atualizada com sucesso",
                                data={"issue_key": issue_key}
                            )
                            
                            return updated_issue
                        else:
                            return None
                    else:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.ERROR,
                            "Falha ao atualizar issue",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return None
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "jira_integration"})
            return None
    
    async def get_project_issues(self, status: str = None, assignee: str = None) -> List[JiraIssue]:
        """Obtém issues do projeto"""
        try:
            jql = f"project = {self.project_key}"
            
            if status:
                jql += f" AND status = '{status}'"
            if assignee:
                jql += f" AND assignee = '{assignee}'"
            
            params = {"jql": jql, "maxResults": 100}
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/rest/api/2/search"
                async with session.get(url, auth=aiohttp.BasicAuth(self.username, self.password), 
                                     params=params) as response:
                    if response.status == 200:
                        search_data = await response.json()
                        
                        issues = []
                        for issue_data in search_data["issues"]:
                            fields = issue_data["fields"]
                            
                            issue = JiraIssue(
                                key=issue_data["key"],
                                summary=fields["summary"],
                                description=fields.get("description", ""),
                                status=fields["status"]["name"],
                                priority=fields["priority"]["name"],
                                assignee=fields["assignee"]["displayName"] if fields["assignee"] else "Unassigned",
                                reporter=fields["reporter"]["displayName"],
                                created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")),
                                updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")),
                                labels=fields.get("labels", []),
                                components=[comp["name"] for comp in fields.get("components", [])]
                            )
                            issues.append(issue)
                        
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.INFO,
                            "Issues do projeto obtidas com sucesso",
                            data={"count": len(issues), "project": self.project_key}
                        )
                        
                        return issues
                    else:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.ERROR,
                            "Falha ao obter issues do projeto",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return []
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "jira_integration"})
            return []
    
    async def get_sprints(self, board_id: int) -> List[JiraSprint]:
        """Obtém sprints do board"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.url}/rest/agile/1.0/board/{board_id}/sprint"
                async with session.get(url, auth=aiohttp.BasicAuth(self.username, self.password)) as response:
                    if response.status == 200:
                        sprints_data = await response.json()
                        
                        sprints = []
                        for sprint_data in sprints_data["values"]:
                            sprint = JiraSprint(
                                id=sprint_data["id"],
                                name=sprint_data["name"],
                                state=sprint_data["state"],
                                start_date=datetime.fromisoformat(sprint_data["startDate"].replace("Z", "+00:00")) if sprint_data.get("startDate") else None,
                                end_date=datetime.fromisoformat(sprint_data["endDate"].replace("Z", "+00:00")) if sprint_data.get("endDate") else None,
                                goal=sprint_data.get("goal", "")
                            )
                            sprints.append(sprint)
                        
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.INFO,
                            "Sprints obtidos com sucesso",
                            data={"count": len(sprints), "board_id": board_id}
                        )
                        
                        return sprints
                    else:
                        self.logger.log_structured(
                            "jira_integration",
                            LogLevel.ERROR,
                            "Falha ao obter sprints",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return []
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "jira_integration"})
            return []
    
    def display_issues(self, issues: List[JiraIssue]):
        """Exibe issues em formato de tabela"""
        if not issues:
            self.console.print("📋 [yellow]Nenhuma issue encontrada[/yellow]")
            return
        
        table = Table(title="📋 Issues do Jira")
        table.add_column("Key", style="cyan")
        table.add_column("Summary", style="white")
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Assignee", style="dim")
        
        for issue in issues:
            table.add_row(
                issue.key,
                issue.summary[:50] + "..." if len(issue.summary) > 50 else issue.summary,
                issue.status,
                issue.priority,
                issue.assignee
            )
        
        self.console.print(table) 