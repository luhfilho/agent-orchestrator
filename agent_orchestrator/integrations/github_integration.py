"""
Integração GitHub - Agent Orchestrator
Integração com GitHub para gerenciar repositórios e issues
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
class GitHubIssue:
    """Issue do GitHub"""
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class GitHubPR:
    """Pull Request do GitHub"""
    number: int
    title: str
    body: str
    state: str
    head_branch: str
    base_branch: str
    created_at: datetime
    updated_at: datetime


class GitHubIntegration:
    """Integração com GitHub"""
    
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.console = Console()
        self.logger = advanced_logger
        
    async def test_connection(self) -> bool:
        """Testa conexão com GitHub"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.INFO,
                            "Conexão com GitHub estabelecida",
                            data={"owner": self.owner, "repo": self.repo}
                        )
                        return True
                    else:
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.ERROR,
                            "Falha na conexão com GitHub",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return False
        except Exception as e:
            self.logger.log_error(e, {"component": "github_integration"})
            return False
    
    async def create_issue(self, title: str, body: str, labels: List[str] = None, 
                          assignees: List[str] = None) -> Optional[GitHubIssue]:
        """Cria issue no GitHub"""
        try:
            data = {
                "title": title,
                "body": body
            }
            
            if labels:
                data["labels"] = labels
            if assignees:
                data["assignees"] = assignees
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 201:
                        issue_data = await response.json()
                        
                        issue = GitHubIssue(
                            number=issue_data["number"],
                            title=issue_data["title"],
                            body=issue_data["body"],
                            state=issue_data["state"],
                            labels=[label["name"] for label in issue_data["labels"]],
                            assignees=[assignee["login"] for assignee in issue_data["assignees"]],
                            created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                        )
                        
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.INFO,
                            "Issue criada com sucesso",
                            data={"issue_number": issue.number, "title": issue.title}
                        )
                        
                        return issue
                    else:
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.ERROR,
                            "Falha ao criar issue",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return None
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "github_integration"})
            return None
    
    async def update_issue(self, issue_number: int, title: str = None, body: str = None,
                          state: str = None, labels: List[str] = None) -> Optional[GitHubIssue]:
        """Atualiza issue no GitHub"""
        try:
            data = {}
            if title:
                data["title"] = title
            if body:
                data["body"] = body
            if state:
                data["state"] = state
            if labels:
                data["labels"] = labels
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}"
                async with session.patch(url, headers=self.headers, json=data) as response:
                    if response.status == 200:
                        issue_data = await response.json()
                        
                        issue = GitHubIssue(
                            number=issue_data["number"],
                            title=issue_data["title"],
                            body=issue_data["body"],
                            state=issue_data["state"],
                            labels=[label["name"] for label in issue_data["labels"]],
                            assignees=[assignee["login"] for assignee in issue_data["assignees"]],
                            created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                        )
                        
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.INFO,
                            "Issue atualizada com sucesso",
                            data={"issue_number": issue.number, "title": issue.title}
                        )
                        
                        return issue
                    else:
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.ERROR,
                            "Falha ao atualizar issue",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return None
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "github_integration"})
            return None
    
    async def create_pull_request(self, title: str, body: str, head_branch: str, 
                                 base_branch: str = "main") -> Optional[GitHubPR]:
        """Cria pull request no GitHub"""
        try:
            data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 201:
                        pr_data = await response.json()
                        
                        pr = GitHubPR(
                            number=pr_data["number"],
                            title=pr_data["title"],
                            body=pr_data["body"],
                            state=pr_data["state"],
                            head_branch=pr_data["head"]["ref"],
                            base_branch=pr_data["base"]["ref"],
                            created_at=datetime.fromisoformat(pr_data["created_at"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(pr_data["updated_at"].replace("Z", "+00:00"))
                        )
                        
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.INFO,
                            "Pull Request criado com sucesso",
                            data={"pr_number": pr.number, "title": pr.title}
                        )
                        
                        return pr
                    else:
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.ERROR,
                            "Falha ao criar Pull Request",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return None
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "github_integration"})
            return None
    
    async def get_issues(self, state: str = "open", labels: List[str] = None) -> List[GitHubIssue]:
        """Obtém issues do GitHub"""
        try:
            params = {"state": state}
            if labels:
                params["labels"] = ",".join(labels)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        issues_data = await response.json()
                        
                        issues = []
                        for issue_data in issues_data:
                            issue = GitHubIssue(
                                number=issue_data["number"],
                                title=issue_data["title"],
                                body=issue_data["body"],
                                state=issue_data["state"],
                                labels=[label["name"] for label in issue_data["labels"]],
                                assignees=[assignee["login"] for assignee in issue_data["assignees"]],
                                created_at=datetime.fromisoformat(issue_data["created_at"].replace("Z", "+00:00")),
                                updated_at=datetime.fromisoformat(issue_data["updated_at"].replace("Z", "+00:00"))
                            )
                            issues.append(issue)
                        
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.INFO,
                            "Issues obtidas com sucesso",
                            data={"count": len(issues), "state": state}
                        )
                        
                        return issues
                    else:
                        self.logger.log_structured(
                            "github_integration",
                            LogLevel.ERROR,
                            "Falha ao obter issues",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return []
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "github_integration"})
            return []
    
    def display_issues(self, issues: List[GitHubIssue]):
        """Exibe issues em formato de tabela"""
        if not issues:
            self.console.print("📋 [yellow]Nenhuma issue encontrada[/yellow]")
            return
        
        table = Table(title="📋 Issues do GitHub")
        table.add_column("Número", style="cyan")
        table.add_column("Título", style="white")
        table.add_column("Estado", style="green")
        table.add_column("Labels", style="yellow")
        table.add_column("Criada", style="dim")
        
        for issue in issues:
            labels_str = ", ".join(issue.labels) if issue.labels else "Nenhuma"
            created_str = issue.created_at.strftime("%d/%m/%Y")
            
            table.add_row(
                str(issue.number),
                issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                issue.state,
                labels_str,
                created_str
            )
        
        self.console.print(table) 