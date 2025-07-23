"""
Testes unitários para o Markdown Backlog Parser
"""

import pytest
import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch, AsyncMock

from agent_orchestrator.utils.markdown_parser import MarkdownBacklogParser, MarkdownBacklogParserError
from agent_orchestrator.models.backlog import Backlog, UserStory


class TestMarkdownBacklogParser:
    """Testes para o parser de markdown"""
    
    @pytest.fixture
    def sample_markdown_content(self):
        """Conteúdo markdown de exemplo"""
        return """# Backlog do Projeto E-commerce

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
- Dependências:"""

    @pytest.fixture
    def temp_markdown_file(self, sample_markdown_content):
        """Arquivo markdown temporário"""
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_markdown_content)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Limpar arquivo temporário
        temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_backlog_title(self, temp_markdown_file):
        """Testa extração do título do backlog"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        assert backlog.title == "Backlog do Projeto E-commerce"
        assert backlog.id == "BL-001"
    
    @pytest.mark.asyncio
    async def test_parse_user_stories(self, temp_markdown_file):
        """Testa extração de user stories"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        assert len(backlog.user_stories) == 3
        
        # Verificar primeira story
        us_001 = backlog.user_stories[0]
        assert us_001.id == "US-001"
        assert us_001.title == "Sistema de autenticação"
        assert us_001.description == "Implementar login e registro de usuários"
        assert us_001.story_points == 8
        assert us_001.priority == "P0"
        assert us_001.dependencies == []
        assert len(us_001.acceptance_criteria) == 4
        
        # Verificar segunda story
        us_002 = backlog.user_stories[1]
        assert us_002.id == "US-002"
        assert us_002.title == "Dashboard do usuário"
        assert us_002.story_points == 5
        assert us_002.priority == "P1"
        assert us_002.dependencies == ["US-001"]
    
    @pytest.mark.asyncio
    async def test_parse_story_with_dependencies(self, temp_markdown_file):
        """Testa parsing de story com dependências"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        us_002 = backlog.user_stories[1]
        assert us_002.dependencies == ["US-001"]
    
    @pytest.mark.asyncio
    async def test_parse_story_without_dependencies(self, temp_markdown_file):
        """Testa parsing de story sem dependências"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        us_001 = backlog.user_stories[0]
        assert us_001.dependencies == []
    
    @pytest.mark.asyncio
    async def test_parse_acceptance_criteria(self, temp_markdown_file):
        """Testa extração de critérios de aceite"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        us_001 = backlog.user_stories[0]
        expected_criteria = [
            "Usuário pode fazer login com email e senha",
            "Usuário pode se registrar com dados básicos",
            "Sistema valida credenciais e retorna erro amigável",
            "Sessão é mantida por 24 horas"
        ]
        
        assert us_001.acceptance_criteria == expected_criteria
    
    @pytest.mark.asyncio
    async def test_parse_story_points(self, temp_markdown_file):
        """Testa extração de story points"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        assert backlog.user_stories[0].story_points == 8
        assert backlog.user_stories[1].story_points == 5
        assert backlog.user_stories[2].story_points == 13
    
    @pytest.mark.asyncio
    async def test_parse_priority(self, temp_markdown_file):
        """Testa extração de prioridade"""
        parser = MarkdownBacklogParser(temp_markdown_file)
        backlog = await parser.parse()
        
        assert backlog.user_stories[0].priority == "P0"
        assert backlog.user_stories[1].priority == "P1"
        assert backlog.user_stories[2].priority == "P0"
    
    @pytest.mark.asyncio
    async def test_parse_invalid_story_points(self):
        """Testa parsing com story points inválidos"""
        content = """# Test Backlog

## US-001: Test Story
- Descrição: Test description
- Critérios de aceite:
  - Test criteria
- Pontos: invalid
- Prioridade: P1
- Dependências:"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            # Deve usar valor padrão (1) para pontos inválidos
            assert backlog.user_stories[0].story_points == 1
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_invalid_priority(self):
        """Testa parsing com prioridade inválida"""
        content = """# Test Backlog

## US-001: Test Story
- Descrição: Test description
- Critérios de aceite:
  - Test criteria
- Pontos: 5
- Prioridade: P5
- Dependências:"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            # Deve usar valor padrão (P2) para prioridade inválida
            assert backlog.user_stories[0].priority == "P2"
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_missing_description(self):
        """Testa parsing sem descrição"""
        content = """# Test Backlog

## US-001: Test Story
- Critérios de aceite:
  - Test criteria
- Pontos: 5
- Prioridade: P1
- Dependências:"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            # Deve usar o título como descrição
            assert backlog.user_stories[0].description == "Test Story"
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_multiple_dependencies(self):
        """Testa parsing com múltiplas dependências"""
        content = """# Test Backlog

## US-001: Test Story
- Descrição: Test description
- Critérios de aceite:
  - Test criteria
- Pontos: 5
- Prioridade: P1
- Dependências: US-001, US-002, US-003"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            expected_deps = ["US-001", "US-002", "US-003"]
            assert backlog.user_stories[0].dependencies == expected_deps
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_empty_dependencies(self):
        """Testa parsing com dependências vazias"""
        content = """# Test Backlog

## US-001: Test Story
- Descrição: Test description
- Critérios de aceite:
  - Test criteria
- Pontos: 5
- Prioridade: P1
- Dependências:"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            assert backlog.user_stories[0].dependencies == []
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_file_not_found(self):
        """Testa parsing de arquivo inexistente"""
        non_existent_file = Path("/non/existent/file.md")
        parser = MarkdownBacklogParser(non_existent_file)
        
        with pytest.raises(MarkdownBacklogParserError) as exc_info:
            await parser.parse()
        
        assert "Arquivo não encontrado" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_parse_empty_file(self):
        """Testa parsing de arquivo vazio"""
        content = ""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            # Deve criar backlog com título padrão
            assert backlog.title == "Backlog Importado"
            assert len(backlog.user_stories) == 0
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_no_user_stories(self):
        """Testa parsing sem user stories"""
        content = """# Test Backlog

Este é um backlog sem user stories."""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            assert backlog.title == "Test Backlog"
            assert len(backlog.user_stories) == 0
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_story_with_minimal_info(self):
        """Testa parsing de story com informações mínimas"""
        content = """# Test Backlog

## US-001: Test Story
- Pontos: 3
- Prioridade: P2"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            story = backlog.user_stories[0]
            assert story.id == "US-001"
            assert story.title == "Test Story"
            assert story.description == "Test Story"  # Usa título como descrição
            assert story.story_points == 3
            assert story.priority == "P2"
            assert story.dependencies == []
            assert story.acceptance_criteria == []
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_story_points_minimum(self):
        """Testa valor mínimo de story points"""
        content = """# Test Backlog

## US-001: Test Story
- Descrição: Test description
- Pontos: 0
- Prioridade: P1"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            # Deve usar valor mínimo (1) para pontos <= 0
            assert backlog.user_stories[0].story_points == 1
        finally:
            temp_path.unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_parse_complex_acceptance_criteria(self):
        """Testa parsing de critérios de aceite complexos"""
        content = """# Test Backlog

## US-001: Test Story
- Descrição: Test description
- Critérios de aceite:
  - Critério 1 simples
  - Critério 2 com - hífen interno
  - Critério 3 final
- Pontos: 5
- Prioridade: P1
- Dependências:"""
        
        with NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            parser = MarkdownBacklogParser(temp_path)
            backlog = await parser.parse()
            
            expected_criteria = [
                "Critério 1 simples",
                "Critério 2 com - hífen interno",
                "Critério 3 final"
            ]
            
            assert backlog.user_stories[0].acceptance_criteria == expected_criteria
        finally:
            temp_path.unlink(missing_ok=True) 