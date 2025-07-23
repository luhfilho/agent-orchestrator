"""
Markdown Backlog Parser - Agent Orchestrator
Parser assíncrono para backlog em markdown
"""

import re
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from ..models.backlog import UserStory, Backlog

USER_STORY_REGEX = re.compile(r"^##\s*(US-\d+):\s*(.+)$", re.MULTILINE)
FIELD_REGEX = re.compile(r"^-\s*(\w+):\s*(.*)$")
CRITERIA_REGEX = re.compile(r"^-\s*(.+)$")

class MarkdownBacklogParserError(Exception):
    """Exceção personalizada para erros de parsing"""
    pass

class MarkdownBacklogParser:
    """Parser de backlog em markdown"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = ""
        self.backlog_title = ""
        self.user_stories: List[UserStory] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    async def parse(self) -> Backlog:
        """Parse do backlog com tratamento de erros amigável"""
        try:
            await self._read_file()
            self._parse_backlog_title()
            self._parse_user_stories()
            
            # Verificar se há erros críticos
            if self.errors:
                raise MarkdownBacklogParserError(
                    f"Erros encontrados no parsing do backlog:\n" + 
                    "\n".join(f"• {error}" for error in self.errors)
                )
            
            return Backlog(
                id="BL-001",
                title=self.backlog_title or "Backlog Importado",
                description=f"Backlog importado de {self.file_path.name}",
                user_stories=self.user_stories
            )
            
        except FileNotFoundError:
            raise MarkdownBacklogParserError(
                f"❌ Arquivo não encontrado: {self.file_path}\n"
                f"Verifique se o caminho está correto e o arquivo existe."
            )
        except PermissionError:
            raise MarkdownBacklogParserError(
                f"❌ Sem permissão para ler o arquivo: {self.file_path}\n"
                f"Verifique as permissões do arquivo."
            )
        except UnicodeDecodeError as e:
            raise MarkdownBacklogParserError(
                f"❌ Erro de codificação no arquivo: {self.file_path}\n"
                f"O arquivo deve estar em UTF-8. Erro: {str(e)}"
            )
        except Exception as e:
            raise MarkdownBacklogParserError(
                f"❌ Erro inesperado ao processar o arquivo: {self.file_path}\n"
                f"Erro: {str(e)}"
            )
    
    async def _read_file(self):
        """Lê o arquivo com tratamento de erro"""
        try:
            import aiofiles
            async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = await f.read()
                
            if not self.content.strip():
                self.warnings.append("⚠️ Arquivo está vazio")
                
        except FileNotFoundError:
            raise
        except PermissionError:
            raise
        except UnicodeDecodeError:
            raise
        except Exception as e:
            raise MarkdownBacklogParserError(f"Erro ao ler arquivo: {str(e)}")
    
    def _parse_backlog_title(self):
        """Extrai título do backlog"""
        match = re.search(r"^#\s*(.+)$", self.content, re.MULTILINE)
        if match:
            self.backlog_title = match.group(1).strip()
        else:
            self.warnings.append("⚠️ Título do backlog não encontrado (formato: # Título)")
    
    def _parse_user_stories(self):
        """Extrai user stories com validação"""
        stories = []
        for us_match in USER_STORY_REGEX.finditer(self.content):
            us_id = us_match.group(1)
            us_title = us_match.group(2).strip()
            us_block = self._extract_story_block(us_match.end())
            
            try:
                story = self._parse_story_block(us_id, us_title, us_block)
                stories.append(story)
            except Exception as e:
                self.errors.append(f"Erro ao processar {us_id}: {str(e)}")
        
        if not stories:
            self.warnings.append("⚠️ Nenhuma user story encontrada (formato: ## US-001: Título)")
        
        self.user_stories = stories
    
    def _extract_story_block(self, start_pos: int) -> str:
        """Extrai o bloco de texto da user story"""
        next_us = USER_STORY_REGEX.search(self.content, pos=start_pos)
        end_pos = next_us.start() if next_us else len(self.content)
        return self.content[start_pos:end_pos]
    
    def _parse_story_block(self, us_id: str, us_title: str, block: str) -> UserStory:
        """Parse de um bloco de story com validação robusta"""
        description = ""
        acceptance_criteria = []
        story_points = 1  # Valor padrão mínimo
        priority = "P2"   # Valor padrão
        dependencies = []
        lines = block.strip().splitlines()
        criteria_mode = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                if line.lower().startswith("- descrição:"):
                    description = line.split(":", 1)[1].strip()
                    if not description:
                        self.warnings.append(f"⚠️ {us_id}: Descrição vazia")
                elif line.lower().startswith("- critérios de aceite:"):
                    criteria_mode = True
                elif line.lower().startswith("- pontos:"):
                    try:
                        points_str = line.split(":", 1)[1].strip()
                        story_points = int(points_str)
                        if story_points < 1:
                            self.warnings.append(f"⚠️ {us_id}: Pontos devem ser >= 1, usando valor padrão")
                            story_points = 1
                    except (ValueError, IndexError):
                        self.warnings.append(f"⚠️ {us_id}: Pontos inválidos '{points_str}', usando valor padrão")
                        story_points = 1
                    criteria_mode = False
                elif line.lower().startswith("- prioridade:"):
                    try:
                        priority = line.split(":", 1)[1].strip()
                        if priority not in ["P0", "P1", "P2", "P3"]:
                            self.warnings.append(f"⚠️ {us_id}: Prioridade inválida '{priority}', usando P2")
                            priority = "P2"
                    except (IndexError):
                        self.warnings.append(f"⚠️ {us_id}: Prioridade não especificada, usando P2")
                        priority = "P2"
                    criteria_mode = False
                elif line.lower().startswith("- dependências:"):
                    try:
                        dep_str = line.split(":", 1)[1].strip()
                        dependencies = [d.strip() for d in dep_str.split(",") if d.strip()]
                    except (IndexError):
                        dependencies = []
                    criteria_mode = False
                elif criteria_mode and line.startswith("- "):
                    criteria = line[2:].strip()
                    if criteria:
                        acceptance_criteria.append(criteria)
                else:
                    criteria_mode = False
                    
            except Exception as e:
                self.errors.append(f"Erro na linha {line_num} de {us_id}: {str(e)}")
        
        # Validações finais
        if not description:
            description = us_title
            self.warnings.append(f"⚠️ {us_id}: Usando título como descrição")
        
        # Validar dependências
        for dep_id in dependencies:
            if not re.match(r"^US-\d+$", dep_id):
                self.warnings.append(f"⚠️ {us_id}: Dependência '{dep_id}' não está no formato US-XXX")
        
        return UserStory(
            id=us_id,
            title=us_title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            story_points=story_points,
            priority=priority,
            dependencies=dependencies
        )
    
    def get_warnings(self) -> List[str]:
        """Retorna lista de warnings"""
        return self.warnings.copy()
    
    def get_errors(self) -> List[str]:
        """Retorna lista de erros"""
        return self.errors.copy()
    
    def has_warnings(self) -> bool:
        """Verifica se há warnings"""
        return len(self.warnings) > 0
    
    def has_errors(self) -> bool:
        """Verifica se há erros"""
        return len(self.errors) > 0 