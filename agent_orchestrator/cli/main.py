"""
CLI - Agent Orchestrator
Interface de linha de comando principal
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.engine import OrchestratorEngine, EngineConfig
from ..utils.logger import logger
from ..auth.login_manager import LoginManager
from ..models.user import User

console = Console()


@click.group()
@click.version_option(version="1.0.0")
@click.option("--verbose", "-v", is_flag=True, help="Modo verboso")
@click.option("--log-level", default="INFO", help="Nível de log")
def cli(verbose: bool, log_level: str):
    """
    🚀 Agent Orchestrator - Orquestrador de Agentes de IA
    
    Transforma backlogs em sprints detalhadas e executa tasks
    usando agentes Claude Code e Gemini CLI.
    
    Exemplos:
        agent_orchestrator analyze-backlog backlog.md
        agent_orchestrator generate-sprint backlog.md --points 20
        agent_orchestrator execute-task TASK-001
    """
    if verbose:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel(log_level)


@cli.command()
@click.argument("username")
@click.password_option()
def login(username: str, password: str):
    """
    Realiza o login do usuário
    """
    login_manager = LoginManager()
    user = login_manager.login(username, password)
    if user:
        console.print(f"✅ [green]Login bem-sucedido para o usuário: {username}[/green]")
    else:
        console.print(f"❌ [red]Falha no login. Verifique suas credenciais.[/red]")

@cli.command()
@click.argument("username")
@click.password_option()
def register(username: str, password: str):
    """
    Registra um novo usuário
    """
    login_manager = LoginManager()
    user = User(username=username, password=password)
    if login_manager.register(user):
        console.print(f"✅ [green]Usuário registrado com sucesso: {username}[/green]")
    else:
        console.print(f"❌ [red]O usuário já existe.[/red]")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(), help="Arquivo de saída")
def analyze_backlog(file_path: Path, output: Optional[Path]):
    """
    Analisa um arquivo de backlog em markdown
    
    FILE_PATH: Caminho para o arquivo de backlog (.md)
    """
    console.print(f"🔍 [bold blue]Analisando backlog:[/bold blue] {file_path}")
    
    async def run_analysis():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Analisar backlog
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analisando backlog...", total=None)
                
                backlog = await engine.analyze_backlog(file_path)
                
                progress.update(task, description="Backlog analisado com sucesso!")
            
            # Exibir resultados
            display_backlog_analysis(backlog)
            
            # Exportar se solicitado
            if output:
                export_backlog_analysis(backlog, output)
                console.print(f"✅ [green]Resultados exportados para:[/green] {output}")
            
        except Exception as e:
            console.print(f"❌ [red]Erro na análise:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_analysis())


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--points", "-p", default=20, help="Pontos máximos do sprint")
@click.option("--priority", "-P", default="P1", help="Prioridade mínima")
@click.option("--output", "-o", type=click.Path(), help="Arquivo de saída")
def generate_sprint(file_path: Path, points: int, priority: str, output: Optional[Path]):
    """
    Gera um sprint baseado no backlog
    
    FILE_PATH: Caminho para o arquivo de backlog (.md)
    """
    console.print(f"🏃 [bold blue]Gerando sprint:[/bold blue] {points} pontos, prioridade {priority}")
    
    async def run_generation():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Analisar backlog
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analisando backlog...", total=None)
                backlog = await engine.analyze_backlog(file_path)
                progress.update(task, description="Gerando sprint...")
                
                sprint = await engine.generate_sprint(backlog, points, priority)
                progress.update(task, description="Sprint gerado com sucesso!")
            
            # Exibir resultados
            display_sprint_generation(sprint)
            
            # Exportar se solicitado
            if output:
                export_sprint(sprint, output)
                console.print(f"✅ [green]Sprint exportado para:[/green] {output}")
            
        except Exception as e:
            console.print(f"❌ [red]Erro na geração:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_generation())


@cli.command()
@click.argument("task_id")
@click.option("--agent", "-a", default="claude", help="Tipo de agente (claude/gemini/auto)")
@click.option("--sprint", "-s", help="ID do sprint para contexto")
def execute_task(task_id: str, agent: str, sprint: Optional[str]):
    """
    Executa uma task específica
    
    TASK_ID: ID da task a ser executada
    """
    console.print(f"⚡ [bold blue]Executando task:[/bold blue] {task_id}")
    
    async def run_execution():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Buscar sprint se fornecido
            sprint_obj = None
            if sprint:
                console.print(f"🔍 [yellow]Carregando sprint:[/yellow] {sprint}")
                sprint_obj = await engine.storage.load_sprint(sprint)
                if not sprint_obj:
                    console.print(f"❌ [red]Sprint {sprint} não encontrado[/red]")
                    sys.exit(1)
            
            # Criar task baseada no contexto
            from ..models.task import Task
            
            if sprint_obj:
                # Buscar user story no sprint
                user_story = None
                for story in sprint_obj.user_stories:
                    if story.id == task_id:
                        user_story = story
                        break
                
                if user_story:
                    task = Task(
                        id=task_id,
                        title=user_story.title,
                        description=user_story.description,
                        user_story_id=user_story.id,
                        agent_type=agent,
                        priority=user_story.priority,
                        complexity="high" if user_story.story_points > 8 else "medium"
                    )
                else:
                    # Task não encontrada no sprint, criar genérica
                    task = Task(
                        id=task_id,
                        title=f"Task {task_id}",
                        description=f"Descrição da task {task_id}",
                        user_story_id=task_id,
                        agent_type=agent
                    )
            else:
                # Criar task genérica
                task = Task(
                    id=task_id,
                    title=f"Task {task_id}",
                    description=f"Descrição da task {task_id}",
                    user_story_id="US-001",
                    agent_type=agent
                )
            
            # Executar task
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task_progress = progress.add_task("Executando task...", total=None)
                
                result = await engine.execute_task(task_id)
                
                progress.update(task_progress, description="Task executada!")
            
            # Exibir resultados
            display_task_execution(task, result)
            
        except Exception as e:
            console.print(f"❌ [red]Erro na execução:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_execution())


@cli.command()
def list_sprints():
    """
    Lista todos os sprints salvos
    """
    console.print("📋 [bold blue]Listando sprints salvos...[/bold blue]")
    
    async def run_listing():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Carregar sprints
            sprints = await engine.storage.list_sprints()
            
            if not sprints:
                console.print("ℹ️ [yellow]Nenhum sprint encontrado[/yellow]")
                console.print("💡 [blue]Use 'agent_orchestrator generate-sprint' para criar um sprint[/blue]")
                return
            
            # Exibir sprints
            table = Table(title="Sprints Salvos")
            table.add_column("ID", style="cyan")
            table.add_column("Nome", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Pontos", style="magenta")
            table.add_column("Stories", style="blue")
            table.add_column("Data Início", style="white")
            table.add_column("Data Fim", style="white")
            
            for sprint in sprints:
                status_color = {
                    "planned": "yellow",
                    "in_progress": "blue", 
                    "completed": "green",
                    "cancelled": "red"
                }.get(sprint.status, "white")
                
                table.add_row(
                    sprint.id,
                    sprint.name,
                    f"[{status_color}]{sprint.status}[/{status_color}]",
                    str(sprint.max_points),
                    str(len(sprint.user_stories)),
                    sprint.start_date.strftime("%Y-%m-%d"),
                    sprint.end_date.strftime("%Y-%m-%d")
                )
            
            console.print(table)
            
            # Estatísticas
            stats = await engine.storage.get_sprint_stats()
            console.print(f"\n📊 [bold]Estatísticas:[/bold]")
            console.print(f"   Total de sprints: {stats['total_sprints']}")
            console.print(f"   Completados: {stats['completed_sprints']}")
            console.print(f"   Em progresso: {stats['in_progress_sprints']}")
            console.print(f"   Planejados: {stats['planned_sprints']}")
            console.print(f"   Total de pontos: {stats['total_points']}")
            console.print(f"   Velocidade média: {stats['average_velocity']:.1f} pontos/dia")
            
        except Exception as e:
            console.print(f"❌ [red]Erro ao listar sprints:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_listing())


@cli.command()
@click.argument("sprint_id")
@click.option("--force", "-f", is_flag=True, help="Forçar deleção sem confirmação")
def delete_sprint(sprint_id: str, force: bool):
    """
    Deleta um sprint salvo
    
    SPRINT_ID: ID do sprint a ser deletado
    """
    console.print(f"🗑️ [bold red]Deletando sprint:[/bold red] {sprint_id}")
    
    async def run_deletion():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Verificar se sprint existe
            sprint = await engine.storage.load_sprint(sprint_id)
            if not sprint:
                console.print(f"❌ [red]Sprint {sprint_id} não encontrado[/red]")
                sys.exit(1)
            
            # Confirmar deleção
            if not force:
                confirm = console.input(f"⚠️ [yellow]Tem certeza que deseja deletar o sprint {sprint_id}? (y/N):[/yellow] ")
                if confirm.lower() not in ['y', 'yes', 'sim']:
                    console.print("❌ [red]Operação cancelada[/red]")
                    return
            
            # Deletar sprint
            success = await engine.storage.delete_sprint(sprint_id)
            
            if success:
                console.print(f"✅ [green]Sprint {sprint_id} deletado com sucesso[/green]")
            else:
                console.print(f"❌ [red]Erro ao deletar sprint {sprint_id}[/red]")
                sys.exit(1)
            
        except Exception as e:
            console.print(f"❌ [red]Erro ao deletar sprint:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_deletion())


@cli.command()
def test_agents():
    """
    Testa a conexão e funcionamento dos agentes
    """
    console.print("🧪 [bold blue]Testando agentes...[/bold blue]")
    
    async def run_test():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Testar agentes
            console.print("\n🔍 Testando Claude Code...")
            claude_agent = engine.orchestrator.agent_factory.get_agent("claude")
            claude_ok = await claude_agent.test_connection()
            
            if claude_ok:
                console.print("✅ [green]Claude Code: OK[/green]")
            else:
                console.print("❌ [red]Claude Code: FALHOU[/red]")
            
            console.print("\n🔍 Testando Gemini CLI...")
            gemini_agent = engine.orchestrator.agent_factory.get_agent("gemini")
            gemini_ok = await gemini_agent.test_connection()
            
            if gemini_ok:
                console.print("✅ [green]Gemini CLI: OK[/green]")
            else:
                console.print("❌ [red]Gemini CLI: FALHOU[/red]")
            
            # Mostrar capacidades
            console.print("\n📊 [bold]Capacidades dos Agentes:[/bold]")
            capabilities = engine.orchestrator.get_agent_capabilities()
            
            for agent_type, caps in capabilities.items():
                console.print(f"\n🤖 [cyan]{caps.name}[/cyan]")
                console.print(f"   Tipo: {caps.type}")
                console.print(f"   Velocidade: {caps.execution_speed}")
                console.print(f"   Complexidade: {caps.complexity_threshold}+ pontos")
                console.print(f"   Custo: ${caps.cost_per_token:.6f}/token")
                console.print(f"   Max Tokens: {caps.max_tokens}")
                
                if caps.personas:
                    console.print(f"   Personas: {', '.join(caps.personas)}")
                
                if caps.mcp_servers:
                    console.print(f"   MCP Servers: {', '.join(caps.mcp_servers)}")
            
            # Resumo
            console.print(f"\n📈 [bold]Resumo:[/bold]")
            console.print(f"   Claude Code: {'✅' if claude_ok else '❌'}")
            console.print(f"   Gemini CLI: {'✅' if gemini_ok else '❌'}")
            
            if claude_ok and gemini_ok:
                console.print("\n🎉 [green]Todos os agentes estão funcionando![/green]")
            else:
                console.print("\n⚠️ [yellow]Alguns agentes falharam. Verifique a configuração.[/yellow]")
            
        except Exception as e:
            console.print(f"❌ [red]Erro no teste:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_test())


@cli.command()
@click.argument("sprint_id")
@click.option("--agent", "-a", default="claude", help="Tipo de agente (claude/gemini/auto)")
@click.option("--rollback/--no-rollback", default=True, help="Habilitar rollback em caso de falha")
@click.option("--notify/--no-notify", default=True, help="Notificar progresso durante execução")
def execute_sprint(sprint_id: str, agent: str, rollback: bool, notify: bool):
    """
    Executa todas as tasks de um sprint
    
    SPRINT_ID: ID do sprint a ser executado
    """
    console.print(f"🏃 [bold blue]Executando sprint:[/bold blue] {sprint_id}")
    console.print(f"📊 [yellow]Configuração:[/yellow] Agente={agent}, Rollback={rollback}, Notificar={notify}")
    
    async def run_execution():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Buscar sprint no storage
            console.print(f"🔍 [yellow]Buscando sprint:[/yellow] {sprint_id}")
            
            sprint = await engine.storage.load_sprint(sprint_id)
            
            if not sprint:
                console.print(f"❌ [red]Sprint {sprint_id} não encontrado[/red]")
                console.print("💡 [blue]Dica: Use 'agent_orchestrator generate-sprint' para criar um sprint[/blue]")
                sys.exit(1)
            
            # Executar sprint com configurações avançadas
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Executando sprint...", total=None)
                
                results = await engine.sprint_executor.execute_sprint(
                    sprint, agent, rollback, notify
                )
                
                progress.update(task, description="Sprint executado!")
            
            # Exibir resultados
            display_sprint_execution(sprint, results)
            
        except Exception as e:
            console.print(f"❌ [red]Erro na execução:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_execution())


@cli.command()
def stats():
    """Exibe estatísticas de execução"""
    console.print("📊 [bold blue]Estatísticas de Execução[/bold blue]")
    
    async def run_stats():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Obter estatísticas
            stats = engine.get_execution_stats()
            sprint_stats = engine.sprint_executor.get_execution_statistics()
            
            # Exibir resultados
            display_execution_stats(stats, sprint_stats)
            
        except Exception as e:
            console.print(f"❌ [red]Erro ao obter estatísticas:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_stats())


@cli.command()
@click.argument("project_type")
@click.argument("project_path", type=click.Path())
@click.option("--validate", "-v", is_flag=True, help="Validar template antes de criar")
def create_project(project_type: str, project_path: Path, validate: bool):
    """Cria estrutura de projeto baseada em template"""
    console.print(f"🏗️ [bold blue]Criando projeto:[/bold blue] {project_type}")
    
    try:
        from ..templates.project_templates import ProjectTemplateManager, ProjectType
        
        # Configurar template manager
        template_manager = ProjectTemplateManager()
        
        # Validar tipo de projeto
        try:
            project_type_enum = ProjectType(project_type)
        except ValueError:
            console.print(f"❌ [red]Tipo de projeto inválido:[/red] {project_type}")
            console.print(f"💡 [blue]Tipos disponíveis:[/blue] {', '.join(t.value for t in ProjectType)}")
            sys.exit(1)
        
        # Validar template se solicitado
        if validate:
            template = template_manager.get_template(project_type_enum)
            if template:
                errors = template_manager.validate_template(template)
                if errors:
                    console.print(f"❌ [red]Template inválido:[/red]")
                    for error in errors:
                        console.print(f"  - {error}")
                    sys.exit(1)
                else:
                    console.print("✅ [green]Template válido[/green]")
        
        # Criar estrutura do projeto
        success = template_manager.create_project_structure(project_type_enum, project_path)
        
        if success:
            console.print(f"✅ [green]Projeto criado com sucesso:[/green] {project_path}")
            console.print(f"📁 [blue]Estrutura criada em:[/blue] {project_path}")
        else:
            console.print(f"❌ [red]Erro ao criar projeto[/red]")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"❌ [red]Erro ao criar projeto:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
def list_templates():
    """Lista templates de projeto disponíveis"""
    console.print("📋 [bold blue]Templates de Projeto Disponíveis[/bold blue]")
    
    try:
        from ..templates.project_templates import ProjectTemplateManager, ProjectType
        
        template_manager = ProjectTemplateManager()
        templates = template_manager.get_all_templates()
        
        table = Table(title="📋 Templates Disponíveis")
        table.add_column("Tipo", style="cyan")
        table.add_column("Nome", style="white")
        table.add_column("Descrição", style="green")
        table.add_column("Dependências", style="yellow")
        
        for project_type, template in templates.items():
            deps = ", ".join(template.dependencies[:3])
            if len(template.dependencies) > 3:
                deps += f" (+{len(template.dependencies) - 3} mais)"
            
            table.add_row(
                project_type.value,
                template.name,
                template.description[:60] + "..." if len(template.description) > 60 else template.description,
                deps
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao listar templates:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("backlog_file", type=click.Path(exists=True, path_type=Path))
@click.option("--points", "-p", default=20, help="Pontos máximos por sprint")
@click.option("--agent", "-a", default="claude", help="Tipo de agente a usar")
@click.option("--rollback/--no-rollback", default=True, help="Habilitar rollback em caso de falha")
@click.option("--pause-on-failure/--no-pause", default=True, help="Pausar em caso de falha")
@click.option("--estimate-time/--no-estimate", default=True, help="Estimar tempo de conclusão")
def execute_backlog(backlog_file: Path, points: int, agent: str, rollback: bool, 
                   pause_on_failure: bool, estimate_time: bool):
    """Executa backlog completo organizando em sprints"""
    console.print(f"📋 [bold blue]Executando backlog:[/bold blue] {backlog_file}")
    console.print(f"📊 [yellow]Configuração:[/yellow] {points} pontos/sprint, Agente={agent}, Rollback={rollback}, Pausar={pause_on_failure}")
    
    async def run_execution():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Analisar backlog
            console.print(f"🔍 [yellow]Analisando backlog:[/yellow] {backlog_file}")
            backlog = await engine.analyze_backlog(backlog_file)
            
            if not backlog.user_stories:
                console.print(f"❌ [red]Backlog não contém user stories[/red]")
                sys.exit(1)
            
            # Executar backlog completo
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Executando backlog...", total=None)
                
                result = await engine.backlog_executor.execute_backlog(
                    backlog, points, agent, rollback, pause_on_failure, estimate_time
                )
                
                progress.update(task, description="Backlog executado!")
            
            # Exibir resultados
            display_backlog_execution(backlog, result)
            
        except Exception as e:
            console.print(f"❌ [red]Erro na execução:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_execution())


@cli.command()
def show_config():
    """Exibe configuração atual"""
    console.print("⚙️ [bold blue]Configuração Atual[/bold blue]")
    
    try:
        from ..config.advanced_config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        summary = config_manager.get_config_summary()
        
        # Resumo da configuração
        table = Table(title="📊 Resumo da Configuração")
        table.add_column("Seção", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Detalhes", style="white")
        
        # Agentes
        agents_status = "✅ Configurado" if summary["agents_configured"]["claude"] or summary["agents_configured"]["gemini"] else "❌ Não configurado"
        agents_details = f"Claude: {'✅' if summary['agents_configured']['claude'] else '❌'}, Gemini: {'✅' if summary['agents_configured']['gemini'] else '❌'}"
        table.add_row("Agentes", agents_status, agents_details)
        
        # Integrações
        integrations_count = sum(summary["integrations_configured"].values())
        integrations_status = f"✅ {integrations_count} configuradas" if integrations_count > 0 else "❌ Nenhuma configurada"
        integrations_details = ", ".join([k for k, v in summary["integrations_configured"].items() if v])
        table.add_row("Integrações", integrations_status, integrations_details or "Nenhuma")
        
        # Performance
        perf_details = f"Tasks: {summary['performance']['max_concurrent_tasks']}, Timeout: {summary['performance']['task_timeout']}s"
        table.add_row("Performance", "✅ Configurado", perf_details)
        
        # Logging
        log_details = f"Nível: {summary['logging']['level']}, JSON: {'✅' if summary['logging']['json_format'] else '❌'}"
        table.add_row("Logging", "✅ Configurado", log_details)
        
        console.print(table)
        
        # Estratégia de reload
        reload_strategy = config.reload_strategy.value
        console.print(f"🔄 [yellow]Estratégia de Reload:[/yellow] {reload_strategy}")
        
        # Arquivo de configuração
        console.print(f"📁 [yellow]Arquivo:[/yellow] {config.config_file}")
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao exibir configuração:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str):
    """Define valor de configuração"""
    console.print(f"⚙️ [bold blue]Definindo configuração:[/bold blue] {key} = {value}")
    
    try:
        from ..config.advanced_config import ConfigManager
        
        config_manager = ConfigManager()
        
        # Converter valor se necessário
        if value.lower() in ["true", "false"]:
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "").isdigit():
            value = float(value)
        
        # Atualizar configuração
        config_manager.update_config({key: value})
        
        console.print(f"✅ [green]Configuração atualizada:[/green] {key} = {value}")
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao atualizar configuração:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--format", "-f", default="yaml", 
              type=click.Choice(["yaml", "json"]),
              help="Formato de exportação")
@click.option("--output", "-o", type=click.Path(), help="Arquivo de saída")
def export_config(format: str, output: Optional[Path]):
    """Exporta configuração atual"""
    console.print(f"📤 [bold blue]Exportando configuração:[/bold blue] {format}")
    
    try:
        from ..config.advanced_config import ConfigManager
        
        config_manager = ConfigManager()
        config_data = config_manager.export_config(format)
        
        if output:
            with open(output, 'w') as f:
                f.write(config_data)
            console.print(f"✅ [green]Configuração exportada:[/green] {output}")
        else:
            console.print(config_data)
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao exportar configuração:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
def import_config(config_file: Path):
    """Importa configuração de arquivo"""
    console.print(f"📥 [bold blue]Importando configuração:[/bold blue] {config_file}")
    
    try:
        from ..config.advanced_config import ConfigManager
        
        config_manager = ConfigManager()
        
        with open(config_file, 'r') as f:
            config_data = f.read()
        
        format = "yaml" if config_file.suffix in [".yaml", ".yml"] else "json"
        config_manager.import_config(config_data, format)
        
        console.print(f"✅ [green]Configuração importada:[/green] {config_file}")
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao importar configuração:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--simple", "-s", is_flag=True, help="Modo simples sem live updates")
@click.option("--components", "-c", multiple=True, 
              type=click.Choice(["overview", "executions", "config", "logs", "performance"]),
              help="Componentes a exibir")
def dashboard(simple: bool, components: tuple):
    """Inicia dashboard de status em tempo real"""
    console.print("📊 [bold blue]Iniciando Dashboard[/bold blue]")
    
    try:
        # Configurar engine
        config = EngineConfig(log_level="INFO")
        engine = OrchestratorEngine(config)
        
        # Criar dashboard
        from ..dashboard.status_dashboard import create_dashboard, DashboardComponent
        dashboard = create_dashboard(engine)
        
        # Converter componentes
        dashboard_components = []
        if components:
            for comp in components:
                if comp == "overview":
                    dashboard_components.append(DashboardComponent.OVERVIEW)
                elif comp == "executions":
                    dashboard_components.append(DashboardComponent.EXECUTIONS)
                elif comp == "config":
                    dashboard_components.append(DashboardComponent.CONFIG)
                elif comp == "logs":
                    dashboard_components.append(DashboardComponent.LOGS)
                elif comp == "performance":
                    dashboard_components.append(DashboardComponent.PERFORMANCE)
        
        if simple:
            console.print("📊 [yellow]Modo simples ativado[/yellow]")
            dashboard.show_simple_dashboard()
        else:
            console.print("📊 [yellow]Modo live ativado[/yellow]")
            dashboard.start_dashboard(dashboard_components)
        
    except Exception as e:
        console.print(f"❌ [red]Erro no dashboard:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
def validate_config():
    """Valida configuração atual"""
    console.print("🔍 [bold blue]Validando configuração[/bold blue]")
    
    try:
        from ..config.advanced_config import ConfigManager
        
        config_manager = ConfigManager()
        errors = config_manager.validate_config()
        
        if errors:
            console.print(f"❌ [red]Configuração inválida:[/red] {len(errors)} erros encontrados")
            for error in errors:
                console.print(f"  - {error}")
            sys.exit(1)
        else:
            console.print("✅ [green]Configuração válida[/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao validar configuração:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
def test_integrations():
    """Testa conexões das integrações externas"""
    console.print("🔗 [bold blue]Testando Integrações Externas[/bold blue]")
    
    async def run_test():
        try:
            from ..integrations.integration_manager import IntegrationManager
            from ..config.advanced_config import ConfigManager
            
            # Carregar configuração
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Criar gerenciador de integrações
            integration_manager = IntegrationManager()
            
            # Registrar integrações baseado na configuração
            integrations_configured = 0
            
            # GitHub
            if config.integrations.github_token:
                if integration_manager.register_github(
                    config.integrations.github_token,
                    "seu-usuario",  # Seria configurável
                    "seu-repo"      # Seria configurável
                ):
                    integrations_configured += 1
            
            # Jira
            if config.integrations.jira_url and config.integrations.jira_username:
                if integration_manager.register_jira(
                    config.integrations.jira_url,
                    config.integrations.jira_username,
                    config.integrations.jira_password or "",
                    "PROJ"  # Seria configurável
                ):
                    integrations_configured += 1
            
            # Slack
            if config.integrations.slack_webhook:
                if integration_manager.register_slack(
                    config.integrations.slack_webhook
                ):
                    integrations_configured += 1
            
            if integrations_configured == 0:
                console.print("⚠️ [yellow]Nenhuma integração configurada[/yellow]")
                console.print("Configure as integrações no arquivo config.yaml")
                return
            
            # Testar conexões
            console.print(f"🔗 [blue]Testando {integrations_configured} integração(ões)...[/blue]")
            results = await integration_manager.test_all_connections()
            
            # Exibir resultados
            integration_manager.display_integration_status()
            
            # Resumo
            successful = sum(1 for connected in results.values() if connected)
            console.print(f"\n📊 [bold]Resumo:[/bold] {successful}/{len(results)} integrações conectadas")
            
        except Exception as e:
            console.print(f"❌ [red]Erro ao testar integrações:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_test())


@cli.command()
@click.argument("integration_type", type=click.Choice(["github", "jira", "slack"]))
@click.argument("config_value")
def configure_integration(integration_type: str, config_value: str):
    """Configura integração externa"""
    console.print(f"⚙️ [bold blue]Configurando Integração: {integration_type.upper()}[/bold blue]")
    
    try:
        from ..config.advanced_config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        if integration_type == "github":
            # config_value seria o token
            config.integrations.github_token = config_value
            console.print("✅ [green]Token do GitHub configurado[/green]")
            
        elif integration_type == "jira":
            # config_value seria a URL
            config.integrations.jira_url = config_value
            console.print("✅ [green]URL do Jira configurada[/green]")
            
        elif integration_type == "slack":
            # config_value seria o webhook
            config.integrations.slack_webhook = config_value
            console.print("✅ [green]Webhook do Slack configurado[/green]")
        
        # Salvar configuração
        config_manager.save_config(config)
        console.print("💾 [blue]Configuração salva[/blue]")
        
    except Exception as e:
        console.print(f"❌ [red]Erro ao configurar integração:[/red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--skip-permissions", is_flag=True, default=True, help="Ativar skip permissions para Claude")
@click.option("--yolo-mode", is_flag=True, default=True, help="Ativar yolo mode para Gemini")
def configure_agents(skip_permissions: bool, yolo_mode: bool):
    """
    Configura opções dos agentes de IA
    
    Opções:
        --skip-permissions: Ativa --dangerously-skip-permissions para Claude Code
        --yolo-mode: Ativa --yolo para Gemini CLI
    """
    console.print("🔧 [bold blue]Configurando agentes...[/bold blue]")
    
    async def run_configuration():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Configurar agentes
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Configurando agentes...", total=None)
                
                # Configurar Claude
                if skip_permissions:
                    engine.agent_factory.configure_claude_skip_permissions(True)
                    console.print("✅ [green]Claude skip permissions ativado[/green]")
                else:
                    engine.agent_factory.configure_claude_skip_permissions(False)
                    console.print("⚠️ [yellow]Claude skip permissions desativado[/yellow]")
                
                # Configurar Gemini
                if yolo_mode:
                    engine.agent_factory.configure_gemini_yolo_mode(True)
                    console.print("✅ [green]Gemini yolo mode ativado[/green]")
                else:
                    engine.agent_factory.configure_gemini_yolo_mode(False)
                    console.print("⚠️ [yellow]Gemini yolo mode desativado[/yellow]")
                
                progress.update(task, description="Agentes configurados!")
            
            console.print("🎉 [bold green]Configuração concluída![/bold green]")
            
        except Exception as e:
            console.print(f"❌ [red]Erro na configuração:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_configuration())


@cli.command()
def agent_status():
    """
    Mostra status dos agentes e suas configurações
    """
    console.print("🤖 [bold blue]Status dos Agentes...[/bold blue]")
    
    async def run_status():
        try:
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Obter status dos agentes
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Verificando agentes...", total=None)
                
                # Testar Claude
                claude_agent = engine.agent_factory.get_agent("claude")
                claude_status = await claude_agent.test_connection()
                
                # Testar Gemini
                gemini_agent = engine.agent_factory.get_agent("gemini")
                gemini_status = await gemini_agent.test_connection()
                
                progress.update(task, description="Status verificado!")
            
            # Exibir status
            display_agent_status(claude_status, gemini_status)
            
        except Exception as e:
            console.print(f"❌ [red]Erro ao verificar status:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_status())


@cli.command()
@click.argument("sprint_id")
@click.option("--format", "-f", default="markdown", 
              type=click.Choice(["markdown", "json", "html", "csv"]),
              help="Formato do relatório")
@click.option("--output", "-o", type=click.Path(), help="Arquivo de saída")
def generate_report(sprint_id: str, format: str, output: Optional[Path]):
    """Gera relatório de progresso do sprint"""
    console.print(f"📊 [bold blue]Gerando relatório:[/bold blue] {sprint_id}")
    
    async def run_report():
        try:
            from ..reporting.progress_reporter import ProgressReporter, ReportFormat
            
            # Configurar engine
            config = EngineConfig(log_level="INFO")
            engine = OrchestratorEngine(config)
            
            # Buscar sprint
            sprint = await engine.storage.load_sprint(sprint_id)
            
            if not sprint:
                console.print(f"❌ [red]Sprint {sprint_id} não encontrado[/red]")
                sys.exit(1)
            
            # Configurar reporter
            reporter = ProgressReporter()
            
            # Gerar relatório
            report_format = ReportFormat(format)
            report_path = reporter.generate_sprint_report(
                sprint, [], report_format  # Lista vazia de resultados por enquanto
            )
            
            # Mover para local especificado se necessário
            if output:
                import shutil
                shutil.move(str(report_path), str(output))
                report_path = output
            
            console.print(f"✅ [green]Relatório gerado:[/green] {report_path}")
            
        except Exception as e:
            console.print(f"❌ [red]Erro ao gerar relatório:[/red] {str(e)}")
            sys.exit(1)
    
    asyncio.run(run_report())


def display_backlog_analysis(backlog):
    """Exibe análise do backlog"""
    table = Table(title=f"📋 Análise do Backlog: {backlog.title}")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Total de Stories", str(len(backlog.user_stories)))
    table.add_row("Total de Pontos", str(backlog.total_points))
    table.add_row("Prioridade Média", backlog.user_stories[0].priority if backlog.user_stories else "N/A")
    
    console.print(table)
    
    # Tabela de stories
    if backlog.user_stories:
        stories_table = Table(title="📝 User Stories")
        stories_table.add_column("ID", style="cyan")
        stories_table.add_column("Título", style="white")
        stories_table.add_column("Pontos", style="green")
        stories_table.add_column("Prioridade", style="yellow")
        
        for story in backlog.user_stories:
            stories_table.add_row(
                story.id,
                story.title[:50] + "..." if len(story.title) > 50 else story.title,
                str(story.story_points),
                story.priority
            )
        
        console.print(stories_table)


def display_sprint_generation(sprint):
    """Exibe geração do sprint"""
    table = Table(title=f"🏃 Sprint Gerado: {sprint.id}")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("ID", sprint.id)
    table.add_row("Nome", sprint.name)
    table.add_row("Stories", str(len(sprint.user_stories)))
    table.add_row("Pontos", str(sum(s.story_points for s in sprint.user_stories)))
    table.add_row("Status", sprint.status)
    
    console.print(table)


def display_task_execution(task, result):
    """Exibe resultado da execução da task"""
    status = "✅ Sucesso" if result.success else "❌ Falha"
    color = "green" if result.success else "red"
    
    panel = Panel(
        f"[bold]{status}[/bold]\n"
        f"Task: {task.id} - {task.title}\n"
        f"Agente: {result.agent_used}\n"
        f"Tempo: {result.execution_time:.2f}s\n"
        f"Mensagem: {result.message}",
        title=f"⚡ Resultado da Execução: {task.id}",
        border_style=color
    )
    
    console.print(panel)


def display_sprint_execution(sprint, results):
    """Exibe resultado da execução do sprint"""
    console.print(f"🏃 [bold blue]Sprint Executado:[/bold blue] {sprint.id}")
    
    # Estatísticas do sprint
    stats_table = Table(title="📊 Estatísticas do Sprint")
    stats_table.add_column("Métrica", style="cyan")
    stats_table.add_column("Valor", style="green")
    
    total_tasks = len(results)
    successful_tasks = len([r for r in results if r.success])
    total_time = sum(r.execution_time for r in results)
    
    stats_table.add_row("Total de Tasks", str(total_tasks))
    stats_table.add_row("Tasks Bem-sucedidas", str(successful_tasks))
    stats_table.add_row("Taxa de Sucesso", f"{(successful_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%")
    stats_table.add_row("Tempo Total", f"{total_time:.2f}s")
    
    console.print(stats_table)
    
    # Detalhes das tasks
    if results:
        tasks_table = Table(title="⚡ Detalhes das Tasks")
        tasks_table.add_column("Status", style="cyan")
        tasks_table.add_column("Agente", style="yellow")
        tasks_table.add_column("Tempo", style="green")
        tasks_table.add_column("Mensagem", style="white")
        
        for result in results:
            status = "✅" if result.success else "❌"
            tasks_table.add_row(
                status,
                result.agent_used,
                f"{result.execution_time:.2f}s",
                result.message[:50] + "..." if len(result.message) > 50 else result.message
            )
        
        console.print(tasks_table)


def display_backlog_execution(backlog, result):
    """Exibe resultados da execução do backlog"""
    console.print(f"\n📋 [bold blue]Resultados da Execução do Backlog[/bold blue]")
    
    # Resumo
    table = Table(title="📊 Resumo da Execução")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Status", result["status"])
    table.add_row("Total de Sprints", str(result["total_sprints"]))
    table.add_row("Sprints Concluídos", str(result["completed_sprints"]))
    table.add_row("Sprints Falharam", str(result["failed_sprints"]))
    table.add_row("Total de Tasks", str(result["total_tasks"]))
    table.add_row("Tasks Concluídas", str(result["completed_tasks"]))
    table.add_row("Tasks Falharam", str(result["failed_tasks"]))
    table.add_row("Tempo de Execução", f"{result['execution_time']:.2f}s")
    
    console.print(table)
    
    # Detalhes dos sprints
    if result["sprints"]:
        sprints_table = Table(title="🏃 Detalhes dos Sprints")
        sprints_table.add_column("Sprint", style="cyan")
        sprints_table.add_column("Status", style="white")
        sprints_table.add_column("Tasks", style="green")
        sprints_table.add_column("Tempo", style="yellow")
        
        for sprint_result in result["sprints"]:
            status = "✅ Sucesso" if sprint_result["success"] else "❌ Falha"
            sprints_table.add_row(
                sprint_result["sprint_id"],
                status,
                f"{sprint_result['completed_tasks']}/{sprint_result['total_tasks']}",
                f"{sprint_result['execution_time']:.2f}s"
            )
        
        console.print(sprints_table)


def display_execution_stats(stats, sprint_stats=None):
    """Exibe estatísticas de execução"""
    table = Table(title="📊 Estatísticas de Execução")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")
    
    table.add_row("Total de Execuções", str(stats.get("total_executions", 0)))
    table.add_row("Execuções Bem-sucedidas", str(stats.get("successful_executions", 0)))
    table.add_row("Taxa de Sucesso", f"{stats.get('success_rate', 0):.1f}%")
    table.add_row("Tempo Médio", f"{stats.get('average_execution_time', 0):.2f}s")
    
    console.print(table)
    
    # Estatísticas por agente
    if stats.get("agent_usage"):
        agent_table = Table(title="🤖 Uso por Agente")
        agent_table.add_column("Agente", style="cyan")
        agent_table.add_column("Execuções", style="green")
        
        for agent, count in stats["agent_usage"].items():
            agent_table.add_row(agent, str(count))
        
        console.print(agent_table)
    
    # Estatísticas de sprint se disponíveis
    if sprint_stats:
        sprint_table = Table(title="🏃 Estatísticas de Sprint")
        sprint_table.add_column("Métrica", style="cyan")
        sprint_table.add_column("Valor", style="green")
        
        sprint_table.add_row("Total de Sprints", str(sprint_stats.get("total_executions", 0)))
        sprint_table.add_row("Sprints Concluídos", str(sprint_stats.get("completed_executions", 0)))
        sprint_table.add_row("Sprints Falharam", str(sprint_stats.get("failed_executions", 0)))
        sprint_table.add_row("Taxa de Sucesso Sprint", f"{sprint_stats.get('success_rate', 0):.1f}%")
        sprint_table.add_row("Total de Tasks", str(sprint_stats.get("total_tasks", 0)))
        sprint_table.add_row("Tasks Concluídas", str(sprint_stats.get("completed_tasks", 0)))
        sprint_table.add_row("Taxa de Sucesso Tasks", f"{sprint_stats.get('task_success_rate', 0):.1f}%")
        
        console.print(sprint_table)


def export_backlog_analysis(backlog, output_path: Path):
    """Exporta análise do backlog"""
    import json
    
    data = {
        "backlog_id": backlog.id,
        "title": backlog.title,
        "description": backlog.description,
        "total_stories": len(backlog.user_stories),
        "total_points": backlog.total_points,
        "user_stories": [
            {
                "id": story.id,
                "title": story.title,
                "description": story.description,
                "story_points": story.story_points,
                "priority": story.priority,
                "dependencies": story.dependencies
            }
            for story in backlog.user_stories
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_sprint(sprint, output_path: Path):
    """Exporta sprint"""
    import json
    
    data = {
        "sprint_id": sprint.id,
        "name": sprint.name,
        "description": sprint.description,
        "max_points": sprint.max_points,
        "status": sprint.status,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "story_points": task.story_points,
                "priority": task.priority,
                "status": task.status
            }
            for task in sprint.tasks
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def display_agent_status(claude_status: bool, gemini_status: bool):
    """Exibe status dos agentes"""
    table = Table(title="🤖 Status dos Agentes")
    table.add_column("Agente", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Configuração", style="yellow")
    
    # Claude
    claude_icon = "✅" if claude_status else "❌"
    claude_status_text = "Conectado" if claude_status else "Desconectado"
    claude_config = "skip_permissions=True" if claude_status else "skip_permissions=False"
    
    table.add_row(
        "Claude Code",
        f"{claude_icon} {claude_status_text}",
        claude_config
    )
    
    # Gemini
    gemini_icon = "✅" if gemini_status else "❌"
    gemini_status_text = "Conectado" if gemini_status else "Desconectado"
    gemini_config = "yolo_mode=True" if gemini_status else "yolo_mode=False"
    
    table.add_row(
        "Gemini CLI",
        f"{gemini_icon} {gemini_status_text}",
        gemini_config
    )
    
    console.print(table)
    
    # Resumo
    total_agents = 2
    connected_agents = sum([claude_status, gemini_status])
    
    console.print(f"\n📊 [bold]Resumo:[/bold] {connected_agents}/{total_agents} agentes conectados")
    
    if connected_agents == 0:
        console.print("⚠️ [yellow]Nenhum agente conectado. Configure os agentes primeiro.[/yellow]")
    elif connected_agents == total_agents:
        console.print("🎉 [green]Todos os agentes estão funcionando![/green]")
    else:
        console.print("⚠️ [yellow]Alguns agentes não estão conectados.[/yellow]")


def main():
    """Entry point do CLI"""
    cli()

if __name__ == "__main__":
    main() 