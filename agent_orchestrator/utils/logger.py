"""
Logger - Agent Orchestrator
Sistema de logging humanizado e intuitivo
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel


class UserFriendlyLogger:
    """Logger amigável ao usuário com feedback visual"""
    
    def __init__(self, name: str = "agent_orchestrator", level: str = "INFO"):
        self.name = name
        self.console = Console()
        self.progress = None
        self.level = getattr(logging, level.upper())
        
        # Configurar logging básico apenas para arquivo se necessário
        self.file_handler = None
        self._file_logger = logging.getLogger(f"{name}_file")
        self._file_logger.setLevel(self.level)
        self._file_logger.propagate = False
    
    def info(self, message: str, **kwargs):
        """Log de informação amigável"""
        if self.level <= logging.INFO:
            self.console.print(f"[blue]ℹ️  {message}[/blue]")
        self._log_to_file("INFO", message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log de sucesso"""
        if self.level <= logging.INFO:
            self.console.print(f"[green]✅ {message}[/green]")
        self._log_to_file("INFO", f"SUCCESS: {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        if self.level <= logging.WARNING:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]")
        self._log_to_file("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de erro"""
        if self.level <= logging.ERROR:
            self.console.print(f"[red]❌ {message}[/red]")
        self._log_to_file("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        if self.level <= logging.DEBUG:
            self.console.print(f"[dim]🔍 {message}[/dim]")
        self._log_to_file("DEBUG", message, **kwargs)
    
    def setLevel(self, level: str):
        """Define o nível de log"""
        self.level = getattr(logging, level.upper())
        self._file_logger.setLevel(self.level)
    
    def log_execution(self, operation: str, duration: float, success: bool, **kwargs):
        """Log estruturado de execução"""
        duration_str = f"{duration:.2f}s"
        
        if success:
            self.console.print(f"[green]✅ {operation} concluído em {duration_str}[/green]")
        else:
            self.console.print(f"[red]❌ {operation} falhou em {duration_str}[/red]")
        
        self._log_to_file("INFO", f"EXECUTION: {operation} - {'SUCCESS' if success else 'FAILED'} - {duration_str}", 
                         operation=operation, duration=duration, success=success, **kwargs)
    
    def log_agent_usage(self, agent_type: str, task_id: str, duration: float, **kwargs):
        """Log de uso de agente"""
        self.console.print(f"[cyan]🤖 {agent_type.capitalize()} executando task {task_id}...[/cyan]")
        self._log_to_file("INFO", f"AGENT USAGE: {agent_type} - Task {task_id} - {duration:.2f}s",
                         agent_type=agent_type, task_id=task_id, duration=duration, **kwargs)
    
    def log_backlog_analysis(self, file_path: str, stories_count: int, total_points: int):
        """Log de análise de backlog"""
        self.console.print(f"[blue]📋 Backlog analisado: {stories_count} stories, {total_points} pontos[/blue]")
        self._log_to_file("INFO", f"BACKLOG ANALYSIS: {file_path} - {stories_count} stories - {total_points} points",
                         file_path=file_path, stories_count=stories_count, total_points=total_points)
    
    def log_sprint_generation(self, sprint_id: str, stories_count: int, points: int):
        """Log de geração de sprint"""
        self.console.print(f"[green]🏃 Sprint {sprint_id} gerado: {stories_count} stories, {points} pontos[/green]")
        self._log_to_file("INFO", f"SPRINT GENERATION: {sprint_id} - {stories_count} stories - {points} points",
                         sprint_id=sprint_id, stories_count=stories_count, points=points)
    
    def log_task_execution(self, task_id: str, status: str, duration: Optional[float] = None):
        """Log de execução de task"""
        duration_str = f" em {duration:.2f}s" if duration else ""
        
        status_config = {
            "pending": ("⏳", "yellow"),
            "running": ("🔄", "blue"), 
            "completed": ("✅", "green"),
            "failed": ("❌", "red"),
            "cancelled": ("⏹️", "dim")
        }
        
        emoji, color = status_config.get(status, ("❓", "white"))
        self.console.print(f"[{color}]{emoji} Task {task_id}: {status}{duration_str}[/{color}]")
        
        self._log_to_file("INFO", f"TASK EXECUTION: {task_id} - {status}{duration_str}",
                         task_id=task_id, status=status, duration=duration)
    
    def start_progress(self, description: str):
        """Inicia indicador de progresso"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        )
        self.progress.start()
        self.task_id = self.progress.add_task(description, total=None)
    
    def update_progress(self, description: str):
        """Atualiza descrição do progresso"""
        if self.progress:
            self.progress.update(self.task_id, description=description)
    
    def stop_progress(self):
        """Para indicador de progresso"""
        if self.progress:
            self.progress.stop()
            self.progress = None
    
    def print_summary(self, title: str, data: Dict[str, Any]):
        """Imprime resumo formatado"""
        content = []
        for key, value in data.items():
            # Formatar chave para ser mais legível
            formatted_key = key.replace("_", " ").title()
            content.append(f"[cyan]{formatted_key}:[/cyan] {value}")
        
        panel = Panel(
            "\n".join(content),
            title=f"[bold]{title}[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
        self.console.print(panel)
    
    def print_error_details(self, error: Exception, context: str = ""):
        """Imprime detalhes de erro de forma amigável"""
        context_str = f" em {context}" if context else ""
        self.console.print(f"[red]❌ Erro{context_str}:[/red] {str(error)}")
        
        # Em modo debug, mostrar traceback
        if self.level <= logging.DEBUG and hasattr(error, '__traceback__'):
            self.console.print_exception(show_locals=True)
    
    def log_to_file(self, file_path: Path, level: str = "INFO"):
        """Configura log para arquivo (apenas estruturado)"""
        if self.file_handler:
            self._file_logger.removeHandler(self.file_handler)
        
        self.file_handler = logging.FileHandler(file_path)
        self.file_handler.setLevel(getattr(logging, level.upper()))
        
        # Formato simples para arquivo
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        self._file_logger.addHandler(self.file_handler)
    
    def _log_to_file(self, level: str, message: str, **kwargs):
        """Log interno para arquivo se configurado"""
        if self.file_handler:
            # Adicionar contexto extra se disponível
            if kwargs:
                extra_info = " | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
                message += extra_info
            
            log_method = getattr(self._file_logger, level.lower())
            log_method(message)


# Instância global do logger
logger = UserFriendlyLogger()