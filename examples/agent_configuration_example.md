# Exemplo de Configuração dos Agentes

Este exemplo demonstra como configurar os agentes Claude Code e Gemini CLI para funcionar sem tokens de API, usando as opções de skip permissions e yolo mode.

## Configuração dos Agentes

### 1. Configurar Skip Permissions para Claude Code

```bash
# Ativar skip permissions (padrão) - para execução automática
agent_orchestrator configure-agents --skip-permissions

# Desativar skip permissions - para execução com aprovação
agent_orchestrator configure-agents --no-skip-permissions
```

### 2. Configurar Yolo Mode para Gemini CLI

```bash
# Ativar yolo mode (padrão) - para execução automática
agent_orchestrator configure-agents --yolo-mode

# Desativar yolo mode - para execução com aprovação
agent_orchestrator configure-agents --no-yolo-mode
```

### 3. Configurar Ambos os Agentes

```bash
# Configurar ambos com as opções padrão (recomendado)
agent_orchestrator configure-agents

# Configurar ambos sem as opções (execução com aprovação)
agent_orchestrator configure-agents --no-skip-permissions --no-yolo-mode
```

## Verificar Status dos Agentes

### 1. Verificar Status Atual

```bash
agent_orchestrator agent-status
```

Exemplo de saída:
```
🤖 Status dos Agentes
┌─────────────┬─────────────────┬─────────────────────┐
│ Agente      │ Status          │ Configuração        │
├─────────────┼─────────────────┼─────────────────────┤
│ Claude Code │ ✅ Conectado    │ skip_permissions=True│
│ Gemini CLI  │ ✅ Conectado    │ yolo_mode=True      │
└─────────────┴─────────────────┴─────────────────────┘

📊 Resumo: 2/2 agentes conectados
🎉 Todos os agentes estão funcionando!
```

### 2. Testar Agentes

```bash
agent_orchestrator test-agents
```

## Uso em Comandos de Execução

### 1. Executar Task com Configuração Automática

```bash
# O sistema usará as configurações definidas
agent_orchestrator execute-task TASK-001
```

### 2. Executar Sprint com Agentes Configurados

```bash
# Executar sprint usando agentes com skip permissions/yolo mode
agent_orchestrator execute-sprint SPRINT-001
```

### 3. Executar Backlog Completo

```bash
# Executar backlog completo com agentes configurados
agent_orchestrator execute-backlog backlog.md
```

## Configuração Avançada

### 1. Configuração via Factory

```python
from agent_orchestrator.agents.factory import AgentFactory

# Criar factory
factory = AgentFactory()

# Configurar Claude
factory.configure_claude_skip_permissions(True)

# Configurar Gemini
factory.configure_gemini_yolo_mode(True)

# Obter agente com configuração específica
claude_agent = factory.get_agent_with_config("claude", skip_permissions=True)
gemini_agent = factory.get_agent_with_config("gemini", yolo_mode=True)
```

### 2. Configuração via Engine

```python
from agent_orchestrator.core.engine import OrchestratorEngine, EngineConfig

# Configurar engine
config = EngineConfig(log_level="INFO")
engine = OrchestratorEngine(config)

# Configurar agentes
engine.agent_factory.configure_claude_skip_permissions(True)
engine.agent_factory.configure_gemini_yolo_mode(True)
```

## Benefícios

### 1. Sem Necessidade de API Keys
- Claude Code funciona sem API key (autenticação local)
- Gemini CLI funciona sem API key (autenticação local)
- Autenticação já configurada nos agentes
- Skip permissions e yolo mode são opções de execução, não de autenticação

### 2. Execução Automática
- Não precisa de aprovação manual para cada ação
- Fluxo contínuo de execução
- Ideal para automação

### 3. Flexibilidade
- Pode ativar/desativar conforme necessário
- Configuração por comando ou programaticamente
- Compatível com diferentes ambientes

## Troubleshooting

### 1. Agente Não Conectado

```bash
# Verificar instalação do Claude Code
claude --version

# Verificar instalação do Gemini CLI
gemini --version

# Testar conexão
agent_orchestrator agent-status
```

### 2. Erro de Permissões

```bash
# Verificar se skip permissions está ativo
agent_orchestrator configure-agents --skip-permissions

# Verificar se yolo mode está ativo
agent_orchestrator configure-agents --yolo-mode
```

### 3. Configuração Reset

```bash
# Resetar configurações para padrão
agent_orchestrator configure-agents

# Verificar status
agent_orchestrator agent-status
```

## Notas Importantes

1. **Autenticação**: Os agentes funcionam sem API keys usando autenticação local
2. **Execução**: Skip permissions e yolo mode controlam apenas o nível de aprovação necessária
3. **Segurança**: As opções `--dangerously-skip-permissions` e `--yolo` devem ser usadas apenas em ambientes confiáveis
4. **Performance**: Os agentes funcionam melhor com essas opções ativadas
5. **Compatibilidade**: Funciona com versões mais recentes dos agentes
6. **Logs**: Todas as ações são logadas para auditoria 