# Exemplo: Funcionamento Sem API Keys

Este exemplo demonstra como o Agent Orchestrator funciona sem necessidade de tokens de API, usando autenticação local dos agentes.

## Configuração Inicial

### 1. Verificar Instalação dos Agentes

```bash
# Verificar Claude Code
claude --version

# Verificar Gemini CLI
gemini --version
```

### 2. Configurar Agentes (Sem API Keys)

```bash
# Configurar para execução automática (recomendado)
agent_orchestrator configure-agents

# Verificar status
agent_orchestrator agent-status
```

## Execução Sem API Keys

### 1. Testar Agentes

```bash
# Testar se os agentes funcionam sem API keys
agent_orchestrator test-agents
```

### 2. Executar Tarefa

```bash
# Executar uma tarefa simples
agent_orchestrator execute-task TASK-001
```

### 3. Analisar Backlog

```bash
# Analisar backlog sem necessidade de API keys
agent_orchestrator analyze-backlog examples/sample_backlog.md
```

## Diferenças Entre Configurações

### Com Skip Permissions/Yolo Mode (Padrão)
```bash
# Configuração automática
agent_orchestrator configure-agents

# Execução sem interrupções
agent_orchestrator execute-task TASK-001
```

### Sem Skip Permissions/Yolo Mode
```bash
# Configuração com aprovação
agent_orchestrator configure-agents --no-skip-permissions --no-yolo-mode

# Execução com aprovação manual
agent_orchestrator execute-task TASK-001
```

## Logs de Exemplo

### Inicialização Sem API Key
```
✅ Claude Code configurado sem API key (autenticação local)
✅ Gemini CLI configurado sem API key (autenticação local)
🔧 Configurando Claude skip_permissions: True
🔧 Configurando Gemini yolo_mode: True
```

### Execução de Tarefa
```
🤖 Auto selecionou agente: claude para task TASK-001
🤖 Executando com persona: dev
✅ Task executada com sucesso usando persona dev
```

## Vantagens da Autenticação Local

### 1. **Simplicidade**
- Não precisa configurar API keys
- Funciona imediatamente após instalação dos agentes
- Menos pontos de falha

### 2. **Segurança**
- Não expõe tokens de API
- Autenticação gerenciada pelos próprios agentes
- Controle local de permissões

### 3. **Flexibilidade**
- Pode usar com ou sem API keys
- Configuração opcional de skip permissions/yolo mode
- Compatível com diferentes ambientes

## Troubleshooting

### Problema: Agente Não Encontrado
```bash
# Verificar instalação
claude --version
gemini --version

# Reinstalar se necessário
npm install -g @anthropic-ai/claude-code
npm install -g @google/gemini-cli
```

### Problema: Erro de Autenticação
```bash
# Verificar se os agentes estão autenticados localmente
claude "teste"
gemini "teste"

# Se necessário, autenticar manualmente
claude auth
gemini auth
```

### Problema: Permissões
```bash
# Verificar configuração atual
agent_orchestrator agent-status

# Reconfigurar se necessário
agent_orchestrator configure-agents
```

## Comparação: Com vs Sem API Keys

| Aspecto | Sem API Keys | Com API Keys |
|---------|--------------|--------------|
| **Configuração** | Simples | Requer tokens |
| **Autenticação** | Local | Externa |
| **Segurança** | Alta | Média |
| **Flexibilidade** | Alta | Limitada |
| **Performance** | Igual | Igual |
| **Compatibilidade** | Universal | Depende de tokens |

## Conclusão

O Agent Orchestrator funciona perfeitamente sem API keys, usando a autenticação local dos agentes Claude Code e Gemini CLI. As opções de skip permissions e yolo mode controlam apenas o nível de aprovação necessária durante a execução, não a autenticação.

### Recomendação
```bash
# Configuração recomendada para uso sem API keys
agent_orchestrator configure-agents

# Verificar se tudo está funcionando
agent_orchestrator agent-status

# Testar execução
agent_orchestrator test-agents
``` 