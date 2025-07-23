# Backlog do Projeto E-commerce

## US-001: Sistema de autenticação
- Descrição: Implementar login e registro de usuários
- Critérios de aceite:
  - Usuário pode fazer login com email e senha
  - Usuário pode se registrar com dados básicos
  - Sistema valida credenciais e retorna erro amigável
  - Sessão é mantida por 24 horas
- Pontos: 8
- Prioridade: P0
- Dependências: 

## US-002: Dashboard do usuário
- Descrição: Interface principal após login
- Critérios de aceite:
  - Mostra informações do usuário logado
  - Exibe histórico de pedidos
  - Interface responsiva para mobile
  - Navegação intuitiva
- Pontos: 5
- Prioridade: P1
- Dependências: US-001

## US-003: Catálogo de produtos
- Descrição: Listagem e busca de produtos
- Critérios de aceite:
  - Lista produtos com imagens e preços
  - Busca por nome e categoria
  - Filtros por preço e avaliação
  - Paginação de resultados
- Pontos: 13
- Prioridade: P0
- Dependências: 

## US-004: Carrinho de compras
- Descrição: Adicionar e gerenciar itens no carrinho
- Critérios de aceite:
  - Adicionar produtos ao carrinho
  - Alterar quantidade de itens
  - Remover itens do carrinho
  - Calcular total automaticamente
- Pontos: 8
- Prioridade: P1
- Dependências: US-003

## US-005: Checkout e pagamento
- Descrição: Finalizar compra com pagamento
- Critérios de aceite:
  - Formulário de dados de entrega
  - Seleção de método de pagamento
  - Validação de dados de pagamento
  - Confirmação de pedido
- Pontos: 13
- Prioridade: P1
- Dependências: US-004

## US-006: Sistema de avaliações
- Descrição: Usuários podem avaliar produtos
- Critérios de aceite:
  - Avaliar produto com estrelas
  - Escrever comentário opcional
  - Mostrar média de avaliações
  - Filtrar por avaliação
- Pontos: 5
- Prioridade: P2
- Dependências: US-003 