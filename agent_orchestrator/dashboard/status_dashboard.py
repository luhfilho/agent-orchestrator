"""
Status Dashboard - Agent Orchestrator
Dashboard de status em tempo real com rich
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.align import Align
from rich.columns import Columns

from ..core.engine import OrchestratorEngine
from ..core.backlog_executor import BacklogExecutor, BacklogExecutionStatus
from ..config.advanced_config import ConfigManager
from ..utils.advanced_logger import advanced_logger, LogLevel


class DashboardComponent(Enum):
    """Componentes do dashboard"""
    OVERVIEW = "overview"
    EXECUTIONS = "executions"
    CONFIG = "config"
    LOGS = "logs"
    PERFORMANCE = "performance"


@dataclass
class DashboardData:
    """Dados do dashboard"""
    timestamp: datetime
    total_executions: int
    active_executions: int
    completed_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time: float
    config_status: Dict[str, Any]
    recent_logs: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class StatusDashboard:
    """Dashboard de status em tempo real"""
    
    def __init__(self, engine: OrchestratorEngine):
        self.engine = engine
        self.console = Console()
        self.logger = advanced_logger
        self.config_manager = ConfigManager()
        self.is_running = False
        self.refresh_interval = 2.0  # segundos
        
    def start_dashboard(self, components: List[DashboardComponent] = None):
        """Inicia dashboard"""
        if components is None:
            components = [DashboardComponent.OVERVIEW, DashboardComponent.EXECUTIONS, DashboardComponent.CONFIG]
        
        self.is_running = True
        self.logger.log_structured(
            "dashboard",
            LogLevel.INFO,
            "Dashboard iniciado",
            data={"components": [c.value for c in components]}
        )
        
        try:
            with Live(self._create_layout(components), refresh_per_second=4, console=self.console) as live:
                while self.is_running:
                    # Atualizar dados
                    dashboard_data = self._collect_dashboard_data()
                    
                    # Atualizar layout
                    live.update(self._create_layout(components, dashboard_data))
                    
                    # Aguardar próximo refresh
                    time.sleep(self.refresh_interval)
                    
        except KeyboardInterrupt:
            self.logger.log_structured(
                "dashboard",
                LogLevel.INFO,
                "Dashboard interrompido pelo usuário"
            )
        except Exception as e:
            self.logger.log_error(e, {"component": "dashboard"})
        finally:
            self.is_running = False
    
    def stop_dashboard(self):
        """Para dashboard"""
        self.is_running = False
        self.logger.log_structured(
            "dashboard",
            LogLevel.INFO,
            "Dashboard parado"
        )
    
    def _collect_dashboard_data(self) -> DashboardData:
        """Coleta dados para o dashboard"""
        try:
            # Estatísticas de execução
            execution_stats = self.engine.backlog_executor.get_execution_statistics()
            
            # Status da configuração
            config_summary = self.config_manager.get_config_summary()
            
            # Logs recentes (simulado)
            recent_logs = self._get_recent_logs()
            
            # Métricas de performance
            performance_metrics = self._get_performance_metrics()
            
            return DashboardData(
                timestamp=datetime.now(),
                total_executions=execution_stats.get("total_executions", 0),
                active_executions=0,  # Seria calculado baseado em execuções em andamento
                completed_executions=execution_stats.get("completed_executions", 0),
                failed_executions=execution_stats.get("failed_executions", 0),
                success_rate=execution_stats.get("success_rate", 0.0),
                avg_execution_time=0.0,  # Seria calculado baseado em dados históricos
                config_status=config_summary,
                recent_logs=recent_logs,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            self.logger.log_error(e, {"component": "dashboard_data_collection"})
            # Retornar dados vazios em caso de erro
            return DashboardData(
                timestamp=datetime.now(),
                total_executions=0,
                active_executions=0,
                completed_executions=0,
                failed_executions=0,
                success_rate=0.0,
                avg_execution_time=0.0,
                config_status={},
                recent_logs=[],
                performance_metrics={}
            )
    
    def _get_recent_logs(self) -> List[Dict[str, Any]]:
        """Obtém logs recentes"""
        # Em implementação real, seria lido do arquivo de log
        return [
            {
                "timestamp": datetime.now() - timedelta(minutes=i),
                "level": "INFO",
                "message": f"Log message {i}",
                "component": "dashboard"
            }
            for i in range(5)
        ]
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de performance"""
        return {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "disk_usage": 23.1,
            "network_io": 12.5,
            "active_connections": 3
        }
    
    def _create_layout(self, components: List[DashboardComponent], 
                      data: DashboardData = None) -> Layout:
        """Cria layout do dashboard"""
        layout = Layout()
        
        # Header
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main")
        )
        
        # Main content
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        # Left column
        layout["left"].split_column(
            Layout(name="overview"),
            Layout(name="executions")
        )
        
        # Right column
        layout["right"].split_column(
            Layout(name="config"),
            Layout(name="logs")
        )
        
        # Preencher componentes
        if DashboardComponent.OVERVIEW in components:
            layout["overview"].update(self._create_overview_panel(data))
        
        if DashboardComponent.EXECUTIONS in components:
            layout["executions"].update(self._create_executions_panel(data))
        
        if DashboardComponent.CONFIG in components:
            layout["config"].update(self._create_config_panel(data))
        
        if DashboardComponent.LOGS in components:
            layout["logs"].update(self._create_logs_panel(data))
        
        # Header sempre presente
        layout["header"].update(self._create_header_panel(data))
        
        return layout
    
    def _create_header_panel(self, data: DashboardData) -> Panel:
        """Cria painel do header"""
        title = Text("🤖 Agent Orchestrator - Dashboard", style="bold blue")
        subtitle = Text(f"Atualizado em: {data.timestamp.strftime('%H:%M:%S') if data else '--:--:--'}", style="dim")
        
        header_content = Align.center(
            Columns([title, subtitle], equal=True),
            vertical="middle"
        )
        
        return Panel(
            header_content,
            title="Status Dashboard",
            border_style="blue"
        )
    
    def _create_overview_panel(self, data: DashboardData) -> Panel:
        """Cria painel de visão geral"""
        if not data:
            return Panel("Carregando...", title="📊 Visão Geral")
        
        # Métricas principais
        metrics_table = Table(show_header=False, box=None)
        metrics_table.add_column("Métrica", style="cyan")
        metrics_table.add_column("Valor", style="green")
        
        metrics_table.add_row("Total de Execuções", str(data.total_executions))
        metrics_table.add_row("Execuções Concluídas", str(data.completed_executions))
        metrics_table.add_row("Execuções Falharam", str(data.failed_executions))
        metrics_table.add_row("Taxa de Sucesso", f"{data.success_rate:.1f}%")
        metrics_table.add_row("Tempo Médio", f"{data.avg_execution_time:.1f}s")
        
        # Status geral
        if data.success_rate >= 80:
            status = "✅ Excelente"
            status_style = "green"
        elif data.success_rate >= 60:
            status = "⚠️ Bom"
            status_style = "yellow"
        else:
            status = "❌ Precisa Melhorar"
            status_style = "red"
        
        status_text = Text(status, style=status_style)
        
        content = Align.center(
            Columns([metrics_table, status_text], equal=True),
            vertical="middle"
        )
        
        return Panel(
            content,
            title="📊 Visão Geral",
            border_style="green"
        )
    
    def _create_executions_panel(self, data: DashboardData) -> Panel:
        """Cria painel de execuções"""
        if not data:
            return Panel("Carregando...", title="🏃 Execuções")
        
        # Lista de execuções recentes
        executions_table = Table(title="Execuções Recentes")
        executions_table.add_column("ID", style="cyan")
        executions_table.add_column("Status", style="white")
        executions_table.add_column("Progresso", style="green")
        executions_table.add_column("Tempo", style="yellow")
        
        # Simular execuções recentes
        recent_executions = [
            ("BL-001", "✅ Concluída", "100%", "2m 30s"),
            ("BL-002", "🔄 Em Andamento", "75%", "1m 45s"),
            ("BL-003", "❌ Falhou", "45%", "3m 12s"),
            ("BL-004", "⏸️ Pausada", "60%", "2m 15s")
        ]
        
        for exec_id, status, progress, time in recent_executions:
            executions_table.add_row(exec_id, status, progress, time)
        
        return Panel(
            executions_table,
            title="🏃 Execuções",
            border_style="blue"
        )
    
    def _create_config_panel(self, data: DashboardData) -> Panel:
        """Cria painel de configuração"""
        if not data:
            return Panel("Carregando...", title="⚙️ Configuração")
        
        config = data.config_status
        
        # Status dos componentes
        config_table = Table(show_header=False, box=None)
        config_table.add_column("Componente", style="cyan")
        config_table.add_column("Status", style="green")
        
        # Agentes
        agents_status = "✅ Configurado" if config.get("agents_configured", {}).get("claude") or config.get("agents_configured", {}).get("gemini") else "❌ Não configurado"
        config_table.add_row("Agentes", agents_status)
        
        # Integrações
        integrations_count = sum(config.get("integrations_configured", {}).values())
        integrations_status = f"✅ {integrations_count} configuradas" if integrations_count > 0 else "❌ Nenhuma"
        config_table.add_row("Integrações", integrations_status)
        
        # Performance
        config_table.add_row("Performance", "✅ Configurado")
        
        # Logging
        config_table.add_row("Logging", "✅ Configurado")
        
        return Panel(
            config_table,
            title="⚙️ Configuração",
            border_style="yellow"
        )
    
    def _create_logs_panel(self, data: DashboardData) -> Panel:
        """Cria painel de logs"""
        if not data:
            return Panel("Carregando...", title="📝 Logs Recentes")
        
        # Logs recentes
        logs_table = Table(title="Logs Recentes")
        logs_table.add_column("Hora", style="cyan", width=8)
        logs_table.add_column("Nível", style="white", width=6)
        logs_table.add_column("Mensagem", style="green")
        
        for log in data.recent_logs[:5]:  # Últimos 5 logs
            time_str = log["timestamp"].strftime("%H:%M:%S")
            level = log["level"]
            message = log["message"][:50] + "..." if len(log["message"]) > 50 else log["message"]
            
            logs_table.add_row(time_str, level, message)
        
        return Panel(
            logs_table,
            title="📝 Logs Recentes",
            border_style="magenta"
        )
    
    def _create_performance_panel(self, data: DashboardData) -> Panel:
        """Cria painel de performance"""
        if not data:
            return Panel("Carregando...", title="📈 Performance")
        
        perf = data.performance_metrics
        
        # Métricas de performance
        perf_table = Table(show_header=False, box=None)
        perf_table.add_column("Métrica", style="cyan")
        perf_table.add_column("Valor", style="green")
        
        perf_table.add_row("CPU", f"{perf.get('cpu_usage', 0):.1f}%")
        perf_table.add_row("Memória", f"{perf.get('memory_usage', 0):.1f}%")
        perf_table.add_row("Disco", f"{perf.get('disk_usage', 0):.1f}%")
        perf_table.add_row("Rede", f"{perf.get('network_io', 0):.1f} MB/s")
        perf_table.add_row("Conexões", str(perf.get('active_connections', 0)))
        
        return Panel(
            perf_table,
            title="📈 Performance",
            border_style="red"
        )
    
    def show_simple_dashboard(self):
        """Mostra dashboard simples sem live updates"""
        console = Console()
        
        console.print(Panel(
            "[bold blue]🤖 Agent Orchestrator - Status Dashboard[/bold blue]\n"
            "[dim]Pressione Ctrl+C para sair[/dim]",
            title="Dashboard",
            border_style="blue"
        ))
        
        try:
            while True:
                # Coletar dados
                data = self._collect_dashboard_data()
                
                # Criar dashboard simples
                dashboard_content = self._create_simple_dashboard_content(data)
                
                # Limpar console e mostrar
                console.clear()
                console.print(dashboard_content)
                
                # Aguardar
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard interrompido[/yellow]")
    
    def _create_simple_dashboard_content(self, data: DashboardData) -> Panel:
        """Cria conteúdo simples para dashboard"""
        # Header
        header = f"[bold blue]🤖 Agent Orchestrator[/bold blue] - {data.timestamp.strftime('%H:%M:%S')}"
        
        # Métricas principais
        metrics = Table(title="📊 Métricas Principais")
        metrics.add_column("Métrica", style="cyan")
        metrics.add_column("Valor", style="green")
        
        metrics.add_row("Total de Execuções", str(data.total_executions))
        metrics.add_row("Execuções Concluídas", str(data.completed_executions))
        metrics.add_row("Taxa de Sucesso", f"{data.success_rate:.1f}%")
        metrics.add_row("Tempo Médio", f"{data.avg_execution_time:.1f}s")
        
        # Status da configuração
        config = Table(title="⚙️ Status da Configuração")
        config.add_column("Componente", style="cyan")
        config.add_column("Status", style="green")
        
        agents_status = "✅ Configurado" if data.config_status.get("agents_configured", {}).get("claude") or data.config_status.get("agents_configured", {}).get("gemini") else "❌ Não configurado"
        config.add_row("Agentes", agents_status)
        
        integrations_count = sum(data.config_status.get("integrations_configured", {}).values())
        integrations_status = f"✅ {integrations_count} configuradas" if integrations_count > 0 else "❌ Nenhuma"
        config.add_row("Integrações", integrations_status)
        
        # Layout em colunas
        content = Columns([
            Panel(metrics, border_style="green"),
            Panel(config, border_style="yellow")
        ])
        
        # Criar painel principal
        main_panel = Panel(
            content,
            title=header,
            border_style="blue"
        )
        
        return main_panel


def create_dashboard(engine: OrchestratorEngine) -> StatusDashboard:
    """Cria instância do dashboard"""
    return StatusDashboard(engine) 