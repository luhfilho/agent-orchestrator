"""
Gerenciador de Integrações - Agent Orchestrator
Coordena todas as integrações externas
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from .github_integration import GitHubIntegration, GitHubIssue, GitHubPR
from .jira_integration import JiraIntegration, JiraIssue, JiraSprint
from .slack_integration import SlackIntegration, SlackMessage
from ..utils.advanced_logger import advanced_logger, LogLevel


@dataclass
class IntegrationStatus:
    """Status de uma integração"""
    name: str
    enabled: bool
    connected: bool
    last_test: datetime
    error_count: int


class IntegrationManager:
    """Gerenciador de integrações externas"""
    
    def __init__(self):
        self.console = Console()
        self.logger = advanced_logger
        self.integrations: Dict[str, Any] = {}
        self.status: Dict[str, IntegrationStatus] = {}
        
    def register_github(self, token: str, owner: str, repo: str) -> bool:
        """Registra integração GitHub"""
        try:
            github = GitHubIntegration(token, owner, repo)
            self.integrations["github"] = github
            self.status["github"] = IntegrationStatus(
                name="GitHub",
                enabled=True,
                connected=False,
                last_test=datetime.now(),
                error_count=0
            )
            
            self.logger.log_structured(
                "integration_manager",
                LogLevel.INFO,
                "Integração GitHub registrada",
                data={"owner": owner, "repo": repo}
            )
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"component": "integration_manager"})
            return False
    
    def register_jira(self, url: str, username: str, password: str, project_key: str) -> bool:
        """Registra integração Jira"""
        try:
            jira = JiraIntegration(url, username, password, project_key)
            self.integrations["jira"] = jira
            self.status["jira"] = IntegrationStatus(
                name="Jira",
                enabled=True,
                connected=False,
                last_test=datetime.now(),
                error_count=0
            )
            
            self.logger.log_structured(
                "integration_manager",
                LogLevel.INFO,
                "Integração Jira registrada",
                data={"url": url, "project": project_key}
            )
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"component": "integration_manager"})
            return False
    
    def register_slack(self, webhook_url: str, default_channel: str = "#general") -> bool:
        """Registra integração Slack"""
        try:
            slack = SlackIntegration(webhook_url, default_channel)
            self.integrations["slack"] = slack
            self.status["slack"] = IntegrationStatus(
                name="Slack",
                enabled=True,
                connected=False,
                last_test=datetime.now(),
                error_count=0
            )
            
            self.logger.log_structured(
                "integration_manager",
                LogLevel.INFO,
                "Integração Slack registrada",
                data={"channel": default_channel}
            )
            return True
            
        except Exception as e:
            self.logger.log_error(e, {"component": "integration_manager"})
            return False
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Testa conexões de todas as integrações"""
        results = {}
        
        for name, integration in self.integrations.items():
            try:
                if hasattr(integration, 'test_connection'):
                    connected = await integration.test_connection()
                    results[name] = connected
                    
                    # Atualizar status
                    if name in self.status:
                        self.status[name].connected = connected
                        self.status[name].last_test = datetime.now()
                        if not connected:
                            self.status[name].error_count += 1
                    
                    self.logger.log_structured(
                        "integration_manager",
                        LogLevel.INFO if connected else LogLevel.ERROR,
                        f"Teste de conexão {name}",
                        data={"connected": connected}
                    )
                else:
                    results[name] = False
                    
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": name})
                results[name] = False
                if name in self.status:
                    self.status[name].error_count += 1
        
        return results
    
    async def notify_task_completion(self, task_id: str, task_title: str, 
                                   status: str, duration: float) -> bool:
        """Notifica conclusão de task via integrações"""
        success_count = 0
        total_count = 0
        
        # Notificar via Slack
        if "slack" in self.integrations and self.status["slack"].connected:
            try:
                success = await self.integrations["slack"].send_task_completion(
                    task_id, task_title, status, duration
                )
                if success:
                    success_count += 1
                total_count += 1
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": "slack"})
                total_count += 1
        
        # Criar issue no GitHub se falhou
        if status == "failed" and "github" in self.integrations and self.status["github"].connected:
            try:
                issue_title = f"Task Falhou: {task_title}"
                issue_body = f"""
Task ID: {task_id}
Título: {task_title}
Status: {status}
Duração: {duration:.2f}s
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Esta task falhou durante a execução e requer atenção.
                """.strip()
                
                await self.integrations["github"].create_issue(
                    issue_title, issue_body, labels=["bug", "task-failed"]
                )
                success_count += 1
                total_count += 1
                
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": "github"})
                total_count += 1
        
        # Criar issue no Jira se falhou
        if status == "failed" and "jira" in self.integrations and self.status["jira"].connected:
            try:
                issue_summary = f"Task Falhou: {task_title}"
                issue_description = f"""
Task ID: {task_id}
Título: {task_title}
Status: {status}
Duração: {duration:.2f}s
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Esta task falhou durante a execução e requer atenção.
                """.strip()
                
                await self.integrations["jira"].create_issue(
                    issue_summary, issue_description, issue_type="Bug", priority="High"
                )
                success_count += 1
                total_count += 1
                
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": "jira"})
                total_count += 1
        
        return success_count > 0 if total_count > 0 else True
    
    async def notify_sprint_progress(self, sprint_id: str, completed_tasks: int, 
                                   total_tasks: int, progress_percentage: float) -> bool:
        """Notifica progresso do sprint via integrações"""
        success_count = 0
        total_count = 0
        
        # Notificar via Slack
        if "slack" in self.integrations and self.status["slack"].connected:
            try:
                success = await self.integrations["slack"].send_sprint_progress(
                    sprint_id, completed_tasks, total_tasks, progress_percentage
                )
                if success:
                    success_count += 1
                total_count += 1
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": "slack"})
                total_count += 1
        
        return success_count > 0 if total_count > 0 else True
    
    async def notify_backlog_completion(self, backlog_id: str, total_sprints: int,
                                      total_tasks: int, total_duration: float) -> bool:
        """Notifica conclusão de backlog via integrações"""
        success_count = 0
        total_count = 0
        
        # Notificar via Slack
        if "slack" in self.integrations and self.status["slack"].connected:
            try:
                success = await self.integrations["slack"].send_backlog_completion(
                    backlog_id, total_sprints, total_tasks, total_duration
                )
                if success:
                    success_count += 1
                total_count += 1
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": "slack"})
                total_count += 1
        
        return success_count > 0 if total_count > 0 else True
    
    async def send_daily_report(self, stats: Dict[str, Any]) -> bool:
        """Envia relatório diário via integrações"""
        success_count = 0
        total_count = 0
        
        # Enviar via Slack
        if "slack" in self.integrations and self.status["slack"].connected:
            try:
                success = await self.integrations["slack"].send_daily_report(stats)
                if success:
                    success_count += 1
                total_count += 1
            except Exception as e:
                self.logger.log_error(e, {"component": "integration_manager", "integration": "slack"})
                total_count += 1
        
        return success_count > 0 if total_count > 0 else True
    
    def get_integration_status(self) -> Dict[str, IntegrationStatus]:
        """Obtém status de todas as integrações"""
        return self.status.copy()
    
    def display_integration_status(self):
        """Exibe status das integrações em formato de tabela"""
        if not self.status:
            self.console.print("🔗 [yellow]Nenhuma integração configurada[/yellow]")
            return
        
        table = Table(title="🔗 Status das Integrações")
        table.add_column("Integração", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Conectado", style="white")
        table.add_column("Último Teste", style="dim")
        table.add_column("Erros", style="red")
        
        for name, status in self.status.items():
            status_text = "✅ Ativo" if status.enabled else "❌ Inativo"
            connected_text = "✅ Sim" if status.connected else "❌ Não"
            last_test = status.last_test.strftime("%d/%m %H:%M")
            errors = str(status.error_count)
            
            table.add_row(
                status.name,
                status_text,
                connected_text,
                last_test,
                errors
            )
        
        self.console.print(table)
    
    def get_available_integrations(self) -> List[str]:
        """Obtém lista de integrações disponíveis"""
        return list(self.integrations.keys())
    
    def is_integration_available(self, name: str) -> bool:
        """Verifica se integração está disponível e conectada"""
        return (name in self.integrations and 
                name in self.status and 
                self.status[name].enabled and 
                self.status[name].connected) 