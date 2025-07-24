# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.0.0] - 2025-07-24

### Changed
- **Agent Padrão**: Claude Code agora é o agente padrão para todas as operações
- **Autenticação Gemini**: Corrigida autenticação para usar padrões do CLI sem forçar API keys
- **Sistema de Logs**: Completamente reescrito para ser 100% humanizado e sem duplicações
- **URLs do Repositório**: Atualizadas todas as URLs para https://github.com/luhfilho/agent-orchestrator/

### Added
- **Guia PyPI**: Documentação completa para publicação no PyPI
- **README Humanizado**: README reescrito com linguagem simples e exemplos práticos

### Fixed
- **Erro 429 Gemini**: Corrigido problema de rate limit com autenticação adequada
- **Logs Duplicados**: Removidas todas as duplicações de log
- **Comando Gemini**: Corrigida sintaxe do comando para usar --prompt

## [1.0.0] - 2025-07-23

### Added

#### Core Engine
- **CLI Principal**: Interface de linha de comando completa com comandos para análise, execução e gerenciamento de backlogs - @luhfilho
- **Core Engine**: Motor principal de orquestração com suporte a múltiplos agentes de IA - @luhfilho
- **Orchestrator**: Sistema de orquestração inteligente que coordena agentes Claude Code e Gemini CLI - @luhfilho
- **Scheduler**: Sistema de agendamento e execução de tarefas com priorização inteligente - @luhfilho
- **Validator**: Sistema de validação de dados e critérios de aceite - @luhfilho
- **Storage**: Sistema de persistência de dados com suporte a JSON e arquivos - @luhfilho

#### Análise e Parsing
- **Backlog Parser**: Parser assíncrono para análise de backlogs em formato markdown - @luhfilho
- **Sprint Parser**: Parser para análise e geração de sprints organizados - @luhfilho
- **Task Parser**: Parser para extração e validação de tarefas individuais - @luhfilho
- **Análise de Backlog**: Sistema completo de análise automática de backlogs com detecção de user stories - @luhfilho
- **Geração de Sprint**: Sistema de geração automática de sprints com limite de pontos e priorização - @luhfilho

#### Agentes de IA
- **Claude Agent**: Integração completa com Claude Code para tarefas complexas e análise profunda - @luhfilho
- **Gemini Agent**: Integração com Gemini CLI para execução rápida e prototipagem - @luhfilho
- **Agent Factory**: Sistema de factory para criação e gerenciamento de agentes - @luhfilho
- **Orquestração Inteligente**: Sistema que escolhe automaticamente o agente ideal para cada tarefa - @luhfilho
- **Skip Permissions**: Configuração para usar --dangerously-skip-permissions no Claude Code - @luhfilho
- **Yolo Mode**: Configuração para usar --yolo no Gemini CLI - @luhfilho
- **Agent Configuration CLI**: Comandos para configurar opções dos agentes - @luhfilho
- **Agent Status**: Comando para verificar status e configurações dos agentes - @luhfilho
- **Autenticação Local**: Suporte para funcionar sem API keys usando autenticação local - @luhfilho

#### Execução e Controle
- **Task Executor**: Sistema de execução de tarefas individuais com rollback automático - @luhfilho
- **Sprint Executor**: Sistema de execução de sprints completos com controle de dependências - @luhfilho
- **Backlog Executor**: Sistema de execução de backlogs completos com progresso em tempo real - @luhfilho
- **Rollback System**: Sistema de rollback automático em caso de falhas - @luhfilho

#### Logs e Monitoramento
- **Sistema de Logs**: Sistema avançado de logging com diferentes níveis e formatos - @luhfilho
- **Performance Logger**: Logger específico para métricas de performance - @luhfilho
- **Execution Logger**: Logger para acompanhamento de execuções - @luhfilho
- **Agent Logger**: Logger específico para comunicação com agentes - @luhfilho

#### Relatórios e Métricas
- **Progress Reporter**: Sistema de geração de relatórios de progresso detalhados - @luhfilho
- **Backlog Reports**: Relatórios específicos para análise de backlogs - @luhfilho
- **Sprint Reports**: Relatórios de execução de sprints com métricas - @luhfilho
- **Burndown Charts**: Cálculo real de burndown charts com dados de execução - @luhfilho
- **Statistics Generator**: Gerador de estatísticas e métricas de projeto - @luhfilho

#### Templates e Configuração
- **Project Templates**: Sistema de templates para diferentes tipos de projeto - @luhfilho
- **Template Manager**: Gerenciador de templates com suporte a múltiplos formatos - @luhfilho
- **Configuration System**: Sistema de configuração avançada com suporte a YAML - @luhfilho
- **Template CLI**: Comandos CLI para gerenciamento de templates - @luhfilho

#### Dashboard e Interface
- **Status Dashboard**: Dashboard de status em tempo real com interface rica - @luhfilho
- **Simple Dashboard**: Modo simples do dashboard para uso rápido - @luhfilho
- **Rich Interface**: Interface rica com cores e formatação usando Rich - @luhfilho
- **Progress Visualization**: Visualização de progresso com barras e indicadores - @luhfilho

#### Integrações Externas
- **GitHub Integration**: Integração completa com GitHub para issues e pull requests - @luhfilho
- **Jira Integration**: Integração com Jira para sincronização de tickets - @luhfilho
- **Slack Integration**: Integração com Slack para notificações e updates - @luhfilho
- **Integration Manager**: Gerenciador centralizado de integrações externas - @luhfilho
- **Integration CLI**: Comandos CLI para teste e configuração de integrações - @luhfilho

#### Testes e Qualidade
- **Unit Tests**: Testes unitários completos para todos os componentes - @luhfilho
- **Integration Tests**: Testes de integração para fluxos completos - @luhfilho
- **Test Coverage**: Cobertura de testes superior a 80% - @luhfilho
- **Test CLI**: Comandos CLI para execução de testes - @luhfilho

#### Utilitários e Ferramentas
- **File Utils**: Utilitários para manipulação de arquivos e diretórios - @luhfilho
- **Validation Utils**: Utilitários de validação e sanitização de dados - @luhfilho
- **Config Utils**: Utilitários para gerenciamento de configuração - @luhfilho
- **Logger Utils**: Utilitários para configuração e gerenciamento de logs - @luhfilho

#### Instalação e Distribuição
- **Pip Installation**: Suporte completo para instalação via pip - @luhfilho
- **Setup.py**: Configuração completa para distribuição via PyPI - @luhfilho
- **Requirements.txt**: Dependências organizadas e versionadas - @luhfilho
- **Pytest Configuration**: Configuração completa para testes automatizados - @luhfilho

#### Documentação
- **README Completo**: Documentação completa com exemplos e guias - @luhfilho
- **CLI Help**: Sistema de ajuda integrado com exemplos detalhados - @luhfilho
- **Code Documentation**: Documentação completa do código com docstrings - @luhfilho
- **Architecture Docs**: Documentação de arquitetura e decisões técnicas - @luhfilho

#### Segurança e Robustez
- **Error Handling**: Sistema robusto de tratamento de erros - @luhfilho
- **Input Validation**: Validação completa de inputs e parâmetros - @luhfilho
- **API Security**: Proteção de APIs e chaves de acesso - @luhfilho
- **Data Sanitization**: Sanitização de dados de entrada - @luhfilho

#### Performance e Otimização
- **Async Processing**: Processamento assíncrono para melhor performance - @luhfilho
- **Caching System**: Sistema de cache para otimização de consultas - @luhfilho
- **Resource Management**: Gerenciamento eficiente de recursos - @luhfilho
- **Memory Optimization**: Otimização de uso de memória - @luhfilho