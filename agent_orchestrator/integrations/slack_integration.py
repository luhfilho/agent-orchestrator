"""
Integração Slack - Agent Orchestrator
Integração com Slack para notificações em tempo real
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
class SlackMessage:
    """Mensagem do Slack"""
    channel: str
    text: str
    attachments: List[Dict[str, Any]]
    timestamp: datetime


class SlackIntegration:
    """Integração com Slack"""
    
    def __init__(self, webhook_url: str, default_channel: str = "#general"):
        self.webhook_url = webhook_url
        self.default_channel = default_channel
        self.console = Console()
        self.logger = advanced_logger
        
    async def test_connection(self) -> bool:
        """Testa conexão com Slack"""
        try:
            test_message = {
                "text": "🤖 Agent Orchestrator - Teste de conexão",
                "channel": self.default_channel
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=test_message) as response:
                    if response.status == 200:
                        self.logger.log_structured(
                            "slack_integration",
                            LogLevel.INFO,
                            "Conexão com Slack estabelecida",
                            data={"channel": self.default_channel}
                        )
                        return True
                    else:
                        self.logger.log_structured(
                            "slack_integration",
                            LogLevel.ERROR,
                            "Falha na conexão com Slack",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return False
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_message(self, text: str, channel: str = None, 
                          attachments: List[Dict[str, Any]] = None) -> bool:
        """Envia mensagem para o Slack"""
        try:
            message = {
                "text": text,
                "channel": channel or self.default_channel
            }
            
            if attachments:
                message["attachments"] = attachments
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    if response.status == 200:
                        self.logger.log_structured(
                            "slack_integration",
                            LogLevel.INFO,
                            "Mensagem enviada com sucesso",
                            data={"channel": message["channel"], "text": text[:50]}
                        )
                        return True
                    else:
                        self.logger.log_structured(
                            "slack_integration",
                            LogLevel.ERROR,
                            "Falha ao enviar mensagem",
                            data={"status": response.status, "response": await response.text()}
                        )
                        return False
                        
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_notification(self, title: str, message: str, color: str = "good",
                               channel: str = None) -> bool:
        """Envia notificação formatada"""
        try:
            attachment = {
                "title": title,
                "text": message,
                "color": color,
                "footer": "Agent Orchestrator",
                "ts": int(datetime.now().timestamp())
            }
            
            return await self.send_message("", channel, [attachment])
            
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_task_completion(self, task_id: str, task_title: str, 
                                  status: str, duration: float, channel: str = None) -> bool:
        """Envia notificação de conclusão de task"""
        try:
            color_map = {
                "success": "good",
                "failed": "danger",
                "warning": "warning"
            }
            
            color = color_map.get(status, "good")
            
            attachment = {
                "title": f"✅ Task Concluída: {task_title}",
                "text": f"**Task ID:** {task_id}\n**Status:** {status}\n**Duração:** {duration:.2f}s",
                "color": color,
                "footer": "Agent Orchestrator",
                "ts": int(datetime.now().timestamp())
            }
            
            return await self.send_message("", channel, [attachment])
            
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_sprint_progress(self, sprint_id: str, completed_tasks: int, 
                                  total_tasks: int, progress_percentage: float,
                                  channel: str = None) -> bool:
        """Envia notificação de progresso do sprint"""
        try:
            progress_bar = "█" * int(progress_percentage / 10) + "░" * (10 - int(progress_percentage / 10))
            
            attachment = {
                "title": f"📊 Progresso do Sprint: {sprint_id}",
                "text": f"**Progresso:** {progress_percentage:.1f}%\n**Tasks:** {completed_tasks}/{total_tasks}\n**Barra:** {progress_bar}",
                "color": "good" if progress_percentage >= 80 else "warning" if progress_percentage >= 50 else "danger",
                "footer": "Agent Orchestrator",
                "ts": int(datetime.now().timestamp())
            }
            
            return await self.send_message("", channel, [attachment])
            
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_error_alert(self, error_message: str, component: str, 
                              channel: str = None) -> bool:
        """Envia alerta de erro"""
        try:
            attachment = {
                "title": f"🚨 Erro Detectado: {component}",
                "text": f"**Erro:** {error_message}\n**Componente:** {component}\n**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "color": "danger",
                "footer": "Agent Orchestrator",
                "ts": int(datetime.now().timestamp())
            }
            
            return await self.send_message("", channel, [attachment])
            
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_daily_report(self, stats: Dict[str, Any], channel: str = None) -> bool:
        """Envia relatório diário"""
        try:
            stats_text = f"""
**📊 Relatório Diário - Agent Orchestrator**

**Execuções:**
• Total: {stats.get('total_executions', 0)}
• Sucessos: {stats.get('successful_executions', 0)}
• Falhas: {stats.get('failed_executions', 0)}
• Taxa de Sucesso: {stats.get('success_rate', 0):.1f}%

**Sprints:**
• Ativos: {stats.get('active_sprints', 0)}
• Concluídos: {stats.get('completed_sprints', 0)}
• Tasks Concluídas: {stats.get('completed_tasks', 0)}

**Performance:**
• Tempo Médio: {stats.get('avg_execution_time', 0):.2f}s
• Uptime: {stats.get('uptime', 0):.1f}%
            """.strip()
            
            attachment = {
                "title": "📈 Relatório Diário",
                "text": stats_text,
                "color": "good",
                "footer": "Agent Orchestrator",
                "ts": int(datetime.now().timestamp())
            }
            
            return await self.send_message("", channel, [attachment])
            
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    async def send_backlog_completion(self, backlog_id: str, total_sprints: int,
                                     total_tasks: int, total_duration: float,
                                     channel: str = None) -> bool:
        """Envia notificação de conclusão de backlog"""
        try:
            duration_hours = total_duration / 3600
            
            attachment = {
                "title": f"🎉 Backlog Concluído: {backlog_id}",
                "text": f"""
**Resumo da Execução:**
• Sprints Executados: {total_sprints}
• Tasks Processadas: {total_tasks}
• Duração Total: {duration_hours:.1f}h
• Status: ✅ Concluído com Sucesso
                """.strip(),
                "color": "good",
                "footer": "Agent Orchestrator",
                "ts": int(datetime.now().timestamp())
            }
            
            return await self.send_message("", channel, [attachment])
            
        except Exception as e:
            self.logger.log_error(e, {"component": "slack_integration"})
            return False
    
    def create_rich_table(self, title: str, data: List[Dict[str, Any]]) -> str:
        """Cria tabela rica para Slack"""
        if not data:
            return f"📋 {title}\nNenhum dado disponível"
        
        # Obter colunas dos dados
        columns = list(data[0].keys())
        
        # Criar cabeçalho
        table = f"📋 {title}\n"
        table += "| " + " | ".join(columns) + " |\n"
        table += "|" + "|".join(["---"] * len(columns)) + "|\n"
        
        # Adicionar linhas
        for row in data:
            table += "| " + " | ".join(str(row.get(col, "")) for col in columns) + " |\n"
        
        return table 