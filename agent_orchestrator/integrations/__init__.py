"""
Integrações Externas - Agent Orchestrator
Módulo para integração com ferramentas externas
"""

from .github_integration import GitHubIntegration
from .jira_integration import JiraIntegration
from .slack_integration import SlackIntegration
from .integration_manager import IntegrationManager

__all__ = [
    "GitHubIntegration",
    "JiraIntegration", 
    "SlackIntegration",
    "IntegrationManager"
] 