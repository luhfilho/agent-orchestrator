#!/usr/bin/env python3
"""
Exemplo Avançado - Agent Orchestrator
Demonstra funcionalidades avançadas do orquestrador
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from agent_orchestrator import (
    OrchestratorEngine, 
    EngineConfig,
    TaskScheduler,
    SchedulerConfig,
    Backlog,
    Sprint,
    Task,
    UserStory
)


async def main():
    """Exemplo avançado de uso"""
    print("🚀 Agent Orchestrator - Exemplo Avançado")
    print("=" * 60)
    
    # 1. Configuração avançada
    print("\n⚙️ 1. Configurando engine avançado...")
    config = EngineConfig(
        max_concurrent_tasks=5,
        timeout_seconds=600,
        default_agent="auto",
        log_level="INFO",
        cache_enabled=True,
        retry_attempts=3
    )
    
    engine = OrchestratorEngine(config)
    
    # 2. Criar backlog complexo
    print("\n📋 2. Criando backlog complexo...")
    backlog = create_complex_backlog()
    print(f"✅ Backlog criado: {len(backlog.user_stories)} stories")
    
    # 3. Análise detalhada do backlog
    print("\n🔍 3. Analisando backlog...")
    backlog.calculate_total_points()
    print(f"   Total de pontos: {backlog.total_points}")
    print(f"   Prioridades: {get_priority_distribution(backlog)}")
    print(f"   Dependências: {count_dependencies(backlog)}")
    
    # 4. Gerar múltiplos sprints
    print("\n🏃 4. Gerando múltiplos sprints...")
    sprints = []
    
    # Sprint 1 - Alta prioridade
    sprint1 = await engine.generate_sprint(backlog, max_points=15, priority="P0")
    sprints.append(sprint1)
    print(f"   Sprint 1: {sprint1.id} - {len(sprint1.user_stories)} stories")
    
    # Sprint 2 - Prioridade média
    sprint2 = await engine.generate_sprint(backlog, max_points=20, priority="P1")
    sprints.append(sprint2)
    print(f"   Sprint 2: {sprint2.id} - {len(sprint2.user_stories)} stories")
    
    # 5. Executar tasks com diferentes agentes
    print("\n🤖 5. Executando tasks com diferentes agentes...")
    
    # Task com Claude
    task_claude = Task(
        id="TASK-101",
        title="Implementar autenticação OAuth",
        description="Sistema de login com Google e GitHub",
        user_story_id="US-001",
        agent_type="claude",
        priority="high",
        complexity="high"
    )
    
    result_claude = await engine.execute_task("TASK-101")
    print(f"   Claude: {result_claude.success} - {result_claude.execution_time:.2f}s")
    
    # Task com Gemini
    task_gemini = Task(
        id="TASK-102",
        title="Criar testes unitários",
        description="Testes para módulo de usuários",
        user_story_id="US-002",
        agent_type="gemini",
        priority="medium",
        complexity="low"
    )
    
    result_gemini = await engine.execute_task("TASK-102")
    print(f"   Gemini: {result_gemini.success} - {result_gemini.execution_time:.2f}s")
    
    # 6. Executar sprint com scheduler
    print("\n📅 6. Usando scheduler para execução...")
    scheduler_config = SchedulerConfig(
        max_concurrent_tasks=3,
        retry_attempts=2,
        retry_delay=3,
        timeout_seconds=300
    )
    
    scheduler = TaskScheduler(scheduler_config)
    
    # Criar tasks para o sprint
    tasks = []
    for i, story in enumerate(sprint1.user_stories):
        task = Task(
            id=f"TASK-{200+i:03d}",
            title=story.title,
            description=story.description,
            user_story_id=story.id,
            agent_type="auto",
            priority="high" if story.priority == "P0" else "medium",
            complexity="high" if story.story_points > 8 else "medium"
        )
        tasks.append(task)
    
    # Agendar tasks
    execution_ids = await scheduler.schedule_multiple_tasks(tasks)
    print(f"   Tasks agendadas: {len(execution_ids)}")
    
    # Aguardar execução
    await asyncio.sleep(5)
    
    # Verificar status
    status = scheduler.get_queue_status()
    print(f"   Status: {status['completed_tasks']} completadas, {status['running_tasks']} rodando")
    
    # 7. Análise de performance
    print("\n📊 7. Análise de performance...")
    stats = engine.get_execution_stats()
    
    print(f"   Total de execuções: {stats['total_executions']}")
    print(f"   Taxa de sucesso: {stats['success_rate']:.1f}%")
    print(f"   Tempo médio: {stats['average_execution_time']:.2f}s")
    
    # Análise por agente
    agent_stats = stats['agent_usage']
    print("   Uso por agente:")
    for agent, count in agent_stats.items():
        print(f"     {agent}: {count} execuções")
    
    # 8. Exportar resultados
    print("\n💾 8. Exportando resultados...")
    export_results(backlog, sprints, stats)
    print("   ✅ Resultados exportados para 'results.json'")
    
    print("\n🎉 Exemplo avançado concluído com sucesso!")


def create_complex_backlog() -> Backlog:
    """Cria um backlog complexo com múltiplas stories"""
    user_stories = [
        UserStory(
            id="US-001",
            title="Sistema de autenticação OAuth",
            description="Implementar login com Google, GitHub e Microsoft",
            acceptance_criteria=[
                "Usuário pode fazer login com Google",
                "Usuário pode fazer login com GitHub", 
                "Usuário pode fazer login com Microsoft",
                "Sistema mantém sessão por 7 dias",
                "Logout limpa todas as sessões"
            ],
            story_points=13,
            priority="P0",
            dependencies=[]
        ),
        UserStory(
            id="US-002",
            title="Dashboard administrativo",
            description="Interface para administradores gerenciarem usuários",
            acceptance_criteria=[
                "Lista todos os usuários",
                "Permite editar permissões",
                "Mostra estatísticas de uso",
                "Interface responsiva"
            ],
            story_points=8,
            priority="P0",
            dependencies=["US-001"]
        ),
        UserStory(
            id="US-003",
            title="Sistema de notificações",
            description="Notificações push e email em tempo real",
            acceptance_criteria=[
                "Notificações push para mobile",
                "Emails automáticos",
                "Configuração de alertas",
                "Histórico de notificações"
            ],
            story_points=5,
            priority="P1",
            dependencies=["US-001"]
        ),
        UserStory(
            id="US-004",
            title="API REST completa",
            description="Endpoints para todas as operações",
            acceptance_criteria=[
                "CRUD completo para usuários",
                "Autenticação via JWT",
                "Documentação Swagger",
                "Rate limiting"
            ],
            story_points=8,
            priority="P1",
            dependencies=["US-001"]
        ),
        UserStory(
            id="US-005",
            title="Testes automatizados",
            description="Suite completa de testes",
            acceptance_criteria=[
                "Testes unitários > 90%",
                "Testes de integração",
                "Testes E2E",
                "CI/CD pipeline"
            ],
            story_points=5,
            priority="P2",
            dependencies=["US-004"]
        ),
        UserStory(
            id="US-006",
            title="Monitoramento e logs",
            description="Sistema de observabilidade",
            acceptance_criteria=[
                "Logs estruturados",
                "Métricas de performance",
                "Alertas automáticos",
                "Dashboard Grafana"
            ],
            story_points=5,
            priority="P2",
            dependencies=["US-004"]
        )
    ]
    
    return Backlog(
        id="BL-002",
        title="Backlog Complexo",
        description="Backlog com múltiplas funcionalidades",
        user_stories=user_stories
    )


def get_priority_distribution(backlog: Backlog) -> dict:
    """Retorna distribuição de prioridades"""
    distribution = {}
    for story in backlog.user_stories:
        priority = story.priority
        distribution[priority] = distribution.get(priority, 0) + 1
    return distribution


def count_dependencies(backlog: Backlog) -> int:
    """Conta total de dependências"""
    total = 0
    for story in backlog.user_stories:
        total += len(story.dependencies)
    return total


def export_results(backlog: Backlog, sprints: list, stats: dict):
    """Exporta resultados para JSON"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "backlog": {
            "id": backlog.id,
            "title": backlog.title,
            "total_stories": len(backlog.user_stories),
            "total_points": backlog.total_points
        },
        "sprints": [
            {
                "id": sprint.id,
                "stories_count": len(sprint.user_stories),
                "points": sum(s.story_points for s in sprint.user_stories)
            }
            for sprint in sprints
        ],
        "execution_stats": stats
    }
    
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main()) 