#!/usr/bin/env python3
"""
Exemplo Básico de Uso - Agent Orchestrator
Demonstra como usar o orquestrador para análise de backlog e execução de tasks
"""

import asyncio
from pathlib import Path
from agent_orchestrator import (
    OrchestratorEngine, 
    EngineConfig,
    Backlog,
    Sprint,
    Task
)


async def main():
    """Exemplo principal de uso"""
    print("🚀 Agent Orchestrator - Exemplo Básico")
    print("=" * 50)
    
    # Configurar engine
    config = EngineConfig(
        max_concurrent_tasks=3,
        timeout_seconds=300,
        default_agent="auto",
        log_level="INFO"
    )
    
    engine = OrchestratorEngine(config)
    
    # 1. Criar backlog de exemplo
    print("\n📋 1. Criando backlog de exemplo...")
    backlog = create_sample_backlog()
    
    # 2. Analisar backlog
    print("\n🔍 2. Analisando backlog...")
    try:
        # Simular análise de arquivo
        backlog = await engine.analyze_backlog(Path("sample_backlog.md"))
        print(f"✅ Backlog analisado: {len(backlog.user_stories)} stories, {backlog.total_points} pontos")
    except FileNotFoundError:
        print("⚠️ Arquivo não encontrado, usando backlog de exemplo")
        print(f"✅ Backlog criado: {len(backlog.user_stories)} stories, {backlog.total_points} pontos")
    
    # 3. Gerar sprint
    print("\n🏃 3. Gerando sprint...")
    sprint = await engine.generate_sprint(backlog, max_points=20, priority="P1")
    print(f"✅ Sprint gerado: {sprint.id}")
    print(f"   Stories: {len(sprint.user_stories)}")
    print(f"   Pontos: {sum(s.story_points for s in sprint.user_stories)}")
    
    # 4. Executar task individual
    print("\n⚡ 4. Executando task individual...")
    task_result = await engine.execute_task("TASK-001", sprint)
    print(f"✅ Task executada: {task_result.success}")
    print(f"   Agente usado: {task_result.agent_used}")
    print(f"   Tempo: {task_result.execution_time:.2f}s")
    
    # 5. Executar sprint completo
    print("\n🏃 5. Executando sprint completo...")
    sprint_results = await engine.execute_sprint(sprint)
    print(f"✅ Sprint executado: {len(sprint_results)} tasks")
    
    successful = sum(1 for r in sprint_results if r.success)
    print(f"   Sucessos: {successful}/{len(sprint_results)}")
    
    # 6. Mostrar estatísticas
    print("\n📊 6. Estatísticas de execução...")
    stats = engine.get_execution_stats()
    print(f"   Total de execuções: {stats['total_executions']}")
    print(f"   Taxa de sucesso: {stats['success_rate']:.1f}%")
    print(f"   Tempo médio: {stats['average_execution_time']:.2f}s")
    
    print("\n🎉 Exemplo concluído com sucesso!")

def create_sample_backlog() -> Backlog:
    """Cria um backlog de exemplo"""
    from agent_orchestrator import UserStory
    
    user_stories = [
        UserStory(
            id="US-001",
            title="Implementar sistema de login",
            description="Sistema de autenticação com email e senha",
            acceptance_criteria=[
                "Usuário pode fazer login com email e senha",
                "Sistema valida credenciais",
                "Sessão é mantida por 24h"
            ],
            story_points=8,
            priority="P0",
            dependencies=[]
        ),
        UserStory(
            id="US-002", 
            title="Dashboard principal",
            description="Interface principal com métricas",
            acceptance_criteria=[
                "Mostra métricas principais",
                "Gráficos interativos",
                "Responsivo para mobile"
            ],
            story_points=13,
            priority="P1",
            dependencies=["US-001"]
        ),
        UserStory(
            id="US-003",
            title="Sistema de notificações",
            description="Notificações em tempo real",
            acceptance_criteria=[
                "Notificações push",
                "Configuração de alertas",
                "Histórico de notificações"
            ],
            story_points=5,
            priority="P2",
            dependencies=["US-001"]
        )
    ]
    
    return Backlog(
        id="BL-001",
        title="Backlog Principal",
        description="Backlog do projeto de exemplo",
        user_stories=user_stories
    )

if __name__ == "__main__":
    print("--- SCRIPT START ---")
    from auth import register_user, login_user

    # Exemplo de autenticação
    print("\n🔐 7. Exemplo de autenticação...")
    
    # Registrar um novo usuário
    success, message = register_user("testuser", "password123")
    print(f"Registro: {message}")

    # Tentar registrar o mesmo usuário novamente
    success, message = register_user("testuser", "password123")
    print(f"Registro (repetido): {message}")

    # Fazer login com o usuário
    success, message = login_user("testuser", "password123")
    print(f"Login (sucesso): {message}")

    # Tentar fazer login com a senha errada
    success, message = login_user("testuser", "wrongpassword")
    print(f"Login (falha): {message}")
    
    print("--- BEFORE MAIN ---")
    asyncio.run(main())
    print("---" + " SCRIPT END ---")