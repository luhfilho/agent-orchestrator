# 🚀 Agent Orchestrator

**Transforme suas ideias em código automaticamente!** O Agent Orchestrator é uma ferramenta que usa IA para automatizar o desenvolvimento de software. Basta escrever o que você quer fazer e ele cuida do resto.

## 🎯 O que é?

Imagine ter dois desenvolvedores experientes trabalhando para você:
- **Claude** 🧠: O arquiteto pensador - planeja, analisa e resolve problemas complexos
- **Gemini** ⚡: O executor rápido - implementa, testa e entrega resultados

O Agent Orchestrator coordena esses dois "desenvolvedores IA" para transformar suas ideias em código real!

## 🎬 Demo Rápida

```bash
# Instalar
pip install agent-orchestrator

# Criar um arquivo com suas ideias
echo "Quero um sistema de blog com posts e comentários" > meu_projeto.md

# Deixar a mágica acontecer!
agent-orchestrator execute-backlog meu_projeto.md
```

Em minutos, você terá o código pronto! 🎉

## 📦 Instalação

### Pré-requisitos
Você precisa ter instalado:
- Python 3.10 ou superior
- Claude CLI ([instruções](https://claude.ai/claude-cli))
- Gemini CLI ([instruções](https://gemini.google.com/cli))

### Instalar o Agent Orchestrator
```bash
pip install agent-orchestrator
```

### Verificar instalação
```bash
agent-orchestrator --version
agent-orchestrator test-agents
```

## 🎮 Como Usar

### 1️⃣ Escreva suas ideias em Markdown

Crie um arquivo `projeto.md`:

```markdown
# Meu Sistema de Tarefas

## Funcionalidades

### TASK-001: Criar tarefas
Como usuário, quero criar novas tarefas com título e descrição
- Deve ter título (obrigatório)
- Deve ter descrição (opcional)
- Deve ter data de criação automática

### TASK-002: Listar tarefas
Como usuário, quero ver todas as minhas tarefas
- Mostrar em ordem de criação
- Mostrar título e status
- Permitir filtrar por status

### TASK-003: Marcar como concluída
Como usuário, quero marcar tarefas como concluídas
- Mudar status para "concluído"
- Registrar data de conclusão
```

### 2️⃣ Execute o comando mágico

```bash
# Opção 1: Executar tudo de uma vez
agent-orchestrator execute-backlog projeto.md

# Opção 2: Ver o que será feito primeiro
agent-orchestrator analyze-backlog projeto.md

# Opção 3: Executar uma tarefa específica
agent-orchestrator execute-task TASK-001
```

### 3️⃣ Acompanhe o progresso

O Agent Orchestrator mostra tudo que está fazendo:

```
🤖 Claude analisando TASK-001...
✅ Análise concluída em 2.3s
🤖 Gemini implementando código...
✅ Arquivo criado: task_manager.py
✅ Testes criados: test_task_manager.py
🎉 Tarefa TASK-001 concluída!
```

## 📚 Exemplos Práticos

### Exemplo 1: API REST Simples

```markdown
# API de Produtos

### TASK-001: Endpoint para listar produtos
Como desenvolvedor, preciso de um endpoint GET /products
- Retornar lista JSON
- Incluir id, nome e preço

### TASK-002: Endpoint para criar produto
Como desenvolvedor, preciso de um endpoint POST /products
- Receber nome e preço
- Validar dados
- Retornar produto criado
```

Comando:
```bash
agent-orchestrator execute-backlog api_produtos.md --agent claude
```

### Exemplo 2: Script de Automação

```markdown
# Automação de Backup

### TASK-001: Backup de arquivos
Como admin, quero fazer backup de uma pasta
- Copiar todos os arquivos
- Comprimir em ZIP
- Adicionar data no nome do arquivo
```

Comando:
```bash
agent-orchestrator execute-task TASK-001 --agent gemini
```

## 🛠️ Comandos Disponíveis

### Análise e Planejamento
```bash
# Analisar um backlog
agent-orchestrator analyze-backlog arquivo.md

# Gerar um sprint (conjunto de tarefas)
agent-orchestrator generate-sprint arquivo.md --points 20
```

### Execução
```bash
# Executar uma tarefa específica
agent-orchestrator execute-task TASK-001

# Executar um backlog completo
agent-orchestrator execute-backlog arquivo.md

# Executar com agente específico
agent-orchestrator execute-task TASK-001 --agent claude  # ou gemini
```

### Configuração e Status
```bash
# Testar conexão com os agentes
agent-orchestrator test-agents

# Ver configurações
agent-orchestrator show-config

# Configurar agentes
agent-orchestrator configure-agents
```

## 📝 Formato do Backlog

O Agent Orchestrator entende markdown simples. Cada tarefa deve ter:

```markdown
### TASK-XXX: Título da tarefa
Descrição do que precisa ser feito
- Detalhe 1
- Detalhe 2
- Detalhe 3
```

**Dicas:**
- Use IDs únicos (TASK-001, FEAT-001, BUG-001)
- Seja claro e específico
- Liste critérios de aceite
- Adicione exemplos quando possível

## 🎯 Casos de Uso

### Para Desenvolvedores Solo
- **Prototipar rapidamente**: Transforme ideias em código funcional
- **Automatizar tarefas chatas**: Deixe a IA fazer o trabalho repetitivo
- **Aprender**: Veja como a IA implementa diferentes soluções

### Para Times
- **Acelerar desenvolvimento**: Complete sprints mais rápido
- **Padronizar código**: IA segue sempre as mesmas práticas
- **Documentar automaticamente**: Código vem com documentação

### Para Estudantes
- **Aprender programação**: Veja exemplos práticos
- **Fazer projetos**: Complete trabalhos mais rápido
- **Entender conceitos**: IA explica o que está fazendo

## 🔧 Configuração Avançada

### Escolher Agente Padrão
```bash
# Claude para tarefas complexas (padrão)
agent-orchestrator execute-task TASK-001 --agent claude

# Gemini para tarefas rápidas
agent-orchestrator execute-task TASK-001 --agent gemini

# Deixar o sistema escolher
agent-orchestrator execute-task TASK-001 --agent auto
```

### Configurar Limites
```bash
# Limitar pontos por sprint
agent-orchestrator generate-sprint backlog.md --points 30

# Definir prioridade mínima
agent-orchestrator generate-sprint backlog.md --priority high
```

## 🐛 Resolução de Problemas

### "Agente não encontrado"
```bash
# Verificar instalação
agent-orchestrator test-agents

# Instalar Claude CLI
npm install -g @anthropic-ai/claude-cli

# Instalar Gemini CLI  
npm install -g @google/gemini-cli
```

### "Erro 429 - Muitas requisições"
- Aguarde alguns minutos
- Use `--agent claude` (geralmente tem limites maiores)
- Configure suas próprias API keys

### "Tarefa falhou"
- Verifique se a descrição está clara
- Adicione mais detalhes e exemplos
- Tente com outro agente

## 🤝 Contribuindo

Adoramos contribuições! Veja como ajudar:

1. Reporte bugs: [Issues](https://github.com/luhfilho/agent-orchestrator/issues)
2. Sugira melhorias: [Discussions](https://github.com/luhfilho/agent-orchestrator/discussions)
3. Envie código: [Pull Requests](https://github.com/luhfilho/agent-orchestrator/pulls)

## 📄 Licença

MIT - Use livremente em seus projetos!

## 🌟 Dicas Finais

1. **Comece simples**: Teste com uma tarefa antes de um backlog completo
2. **Seja específico**: Quanto mais detalhes, melhor o resultado
3. **Itere**: Se o resultado não ficou perfeito, refine a descrição
4. **Experimente**: Cada agente tem seus pontos fortes
5. **Divirta-se**: Deixe a IA trabalhar enquanto você foca no que importa!

---

**Feito com ❤️ pela comunidade Agent Orchestrator**

*Transformando ideias em código, uma tarefa por vez!* 🚀