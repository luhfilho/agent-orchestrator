"""
Project Templates - Agent Orchestrator
Sistema de templates de projeto para diferentes tipos
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from ..utils.advanced_logger import advanced_logger


class ProjectType(Enum):
    """Tipos de projeto disponíveis"""
    WEB_DEVELOPMENT = "web-development"
    API_DEVELOPMENT = "api-development"
    MOBILE_DEVELOPMENT = "mobile-development"
    DATA_SCIENCE = "data-science"
    DESKTOP_APP = "desktop-app"
    MICROSERVICES = "microservices"


@dataclass
class ProjectTemplate:
    """Template de projeto"""
    name: str
    type: ProjectType
    description: str
    structure: Dict[str, Any]
    dependencies: List[str]
    scripts: Dict[str, str]
    config_files: List[str]
    agent_config: Dict[str, Any]
    validation_rules: List[str]


class ProjectTemplateManager:
    """Gerenciador de templates de projeto"""
    
    def __init__(self, templates_dir: Path = Path("./templates")):
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(exist_ok=True)
        self.logger = advanced_logger
        self._load_templates()
    
    def _load_templates(self):
        """Carrega templates disponíveis"""
        self.templates = {
            ProjectType.WEB_DEVELOPMENT: self._create_web_template(),
            ProjectType.API_DEVELOPMENT: self._create_api_template(),
            ProjectType.MOBILE_DEVELOPMENT: self._create_mobile_template(),
            ProjectType.DATA_SCIENCE: self._create_data_science_template(),
            ProjectType.DESKTOP_APP: self._create_desktop_template(),
            ProjectType.MICROSERVICES: self._create_microservices_template()
        }
    
    def _create_web_template(self) -> ProjectTemplate:
        """Cria template para desenvolvimento web"""
        return ProjectTemplate(
            name="Web Development",
            type=ProjectType.WEB_DEVELOPMENT,
            description="Template para desenvolvimento de aplicações web modernas",
            structure={
                "src": {
                    "components": {},
                    "pages": {},
                    "utils": {},
                    "styles": {},
                    "assets": {}
                },
                "public": {},
                "tests": {
                    "unit": {},
                    "integration": {},
                    "e2e": {}
                },
                "docs": {},
                "config": {}
            },
            dependencies=[
                "react", "typescript", "tailwindcss", "jest", "cypress"
            ],
            scripts={
                "dev": "npm run dev",
                "build": "npm run build",
                "test": "npm test",
                "lint": "npm run lint",
                "format": "npm run format"
            },
            config_files=[
                "package.json", "tsconfig.json", "tailwind.config.js",
                "jest.config.js", ".eslintrc.js", ".prettierrc"
            ],
            agent_config={
                "preferred_agent": "claude",
                "persona": "dev",
                "focus_areas": ["frontend", "ui/ux", "performance"]
            },
            validation_rules=[
                "components must be functional",
                "use TypeScript for type safety",
                "implement responsive design",
                "add unit tests for components",
                "optimize for performance"
            ]
        )
    
    def _create_api_template(self) -> ProjectTemplate:
        """Cria template para desenvolvimento de API"""
        return ProjectTemplate(
            name="API Development",
            type=ProjectType.API_DEVELOPMENT,
            description="Template para desenvolvimento de APIs REST/GraphQL",
            structure={
                "src": {
                    "controllers": {},
                    "models": {},
                    "services": {},
                    "middleware": {},
                    "routes": {},
                    "utils": {}
                },
                "tests": {
                    "unit": {},
                    "integration": {},
                    "api": {}
                },
                "docs": {
                    "api": {},
                    "swagger": {}
                },
                "config": {}
            },
            dependencies=[
                "express", "mongoose", "joi", "jest", "supertest"
            ],
            scripts={
                "dev": "npm run dev",
                "start": "npm start",
                "test": "npm test",
                "lint": "npm run lint",
                "docs": "npm run docs"
            },
            config_files=[
                "package.json", "tsconfig.json", "jest.config.js",
                ".eslintrc.js", "swagger.json"
            ],
            agent_config={
                "preferred_agent": "claude",
                "persona": "dev",
                "focus_areas": ["backend", "api-design", "security"]
            },
            validation_rules=[
                "implement proper error handling",
                "add input validation",
                "include API documentation",
                "write integration tests",
                "implement security best practices"
            ]
        )
    
    def _create_mobile_template(self) -> ProjectTemplate:
        """Cria template para desenvolvimento mobile"""
        return ProjectTemplate(
            name="Mobile Development",
            type=ProjectType.MOBILE_DEVELOPMENT,
            description="Template para desenvolvimento de aplicações mobile",
            structure={
                "src": {
                    "components": {},
                    "screens": {},
                    "navigation": {},
                    "services": {},
                    "utils": {},
                    "assets": {}
                },
                "android": {},
                "ios": {},
                "tests": {
                    "unit": {},
                    "integration": {},
                    "e2e": {}
                },
                "docs": {}
            },
            dependencies=[
                "react-native", "expo", "jest", "detox"
            ],
            scripts={
                "start": "expo start",
                "android": "expo run:android",
                "ios": "expo run:ios",
                "test": "npm test",
                "build": "expo build"
            },
            config_files=[
                "package.json", "app.json", "metro.config.js",
                "babel.config.js", "jest.config.js"
            ],
            agent_config={
                "preferred_agent": "claude",
                "persona": "dev",
                "focus_areas": ["mobile", "ui/ux", "performance"]
            },
            validation_rules=[
                "implement responsive design",
                "optimize for mobile performance",
                "add platform-specific code",
                "test on both platforms",
                "follow mobile design guidelines"
            ]
        )
    
    def _create_data_science_template(self) -> ProjectTemplate:
        """Cria template para data science"""
        return ProjectTemplate(
            name="Data Science",
            type=ProjectType.DATA_SCIENCE,
            description="Template para projetos de data science e machine learning",
            structure={
                "src": {
                    "data": {},
                    "models": {},
                    "features": {},
                    "utils": {},
                    "visualization": {}
                },
                "notebooks": {},
                "data": {
                    "raw": {},
                    "processed": {},
                    "external": {}
                },
                "tests": {
                    "unit": {},
                    "integration": {}
                },
                "docs": {}
            },
            dependencies=[
                "pandas", "numpy", "scikit-learn", "matplotlib",
                "seaborn", "jupyter", "pytest"
            ],
            scripts={
                "train": "python src/train.py",
                "evaluate": "python src/evaluate.py",
                "test": "pytest",
                "notebook": "jupyter notebook"
            },
            config_files=[
                "requirements.txt", "setup.py", "pytest.ini",
                "jupyter_notebook_config.py"
            ],
            agent_config={
                "preferred_agent": "claude",
                "persona": "dev",
                "focus_areas": ["data-science", "ml", "analytics"]
            },
            validation_rules=[
                "implement proper data validation",
                "add model evaluation metrics",
                "include data preprocessing",
                "write comprehensive tests",
                "document model performance"
            ]
        )
    
    def _create_desktop_template(self) -> ProjectTemplate:
        """Cria template para aplicações desktop"""
        return ProjectTemplate(
            name="Desktop Application",
            type=ProjectType.DESKTOP_APP,
            description="Template para desenvolvimento de aplicações desktop",
            structure={
                "src": {
                    "main": {},
                    "renderer": {},
                    "shared": {},
                    "assets": {}
                },
                "build": {},
                "tests": {
                    "unit": {},
                    "integration": {}
                },
                "docs": {}
            },
            dependencies=[
                "electron", "typescript", "jest", "spectron"
            ],
            scripts={
                "dev": "npm run dev",
                "build": "npm run build",
                "test": "npm test",
                "package": "npm run package"
            },
            config_files=[
                "package.json", "tsconfig.json", "electron-builder.json",
                "jest.config.js", ".eslintrc.js"
            ],
            agent_config={
                "preferred_agent": "claude",
                "persona": "dev",
                "focus_areas": ["desktop", "ui/ux", "performance"]
            },
            validation_rules=[
                "implement cross-platform compatibility",
                "add proper error handling",
                "optimize for desktop performance",
                "include auto-update functionality",
                "test on multiple platforms"
            ]
        )
    
    def _create_microservices_template(self) -> ProjectTemplate:
        """Cria template para microservices"""
        return ProjectTemplate(
            name="Microservices",
            type=ProjectType.MICROSERVICES,
            description="Template para arquitetura de microservices",
            structure={
                "services": {
                    "auth-service": {},
                    "user-service": {},
                    "product-service": {},
                    "order-service": {}
                },
                "shared": {
                    "lib": {},
                    "config": {}
                },
                "deployment": {
                    "docker": {},
                    "kubernetes": {}
                },
                "tests": {
                    "unit": {},
                    "integration": {},
                    "e2e": {}
                },
                "docs": {}
            },
            dependencies=[
                "express", "docker", "kubernetes", "jest", "supertest"
            ],
            scripts={
                "dev": "docker-compose up",
                "build": "docker build",
                "test": "npm test",
                "deploy": "kubectl apply"
            },
            config_files=[
                "docker-compose.yml", "Dockerfile", "package.json",
                "k8s-deployment.yaml", "jest.config.js"
            ],
            agent_config={
                "preferred_agent": "claude",
                "persona": "dev",
                "focus_areas": ["microservices", "distributed-systems", "devops"]
            },
            validation_rules=[
                "implement service discovery",
                "add circuit breaker pattern",
                "include proper logging",
                "implement health checks",
                "add monitoring and metrics"
            ]
        )
    
    def get_template(self, project_type: ProjectType) -> Optional[ProjectTemplate]:
        """Retorna template para tipo de projeto"""
        return self.templates.get(project_type)
    
    def get_all_templates(self) -> Dict[ProjectType, ProjectTemplate]:
        """Retorna todos os templates disponíveis"""
        return self.templates.copy()
    
    def create_project_structure(self, project_type: ProjectType, 
                               project_path) -> bool:
        """
        Cria estrutura de projeto baseada no template
        
        Args:
            project_type: Tipo de projeto
            project_path: Caminho do projeto
            
        Returns:
            bool: True se criado com sucesso
        """
        template = self.get_template(project_type)
        if not template:
            self.logger.log_structured(
                "templates",
                advanced_logger.LogLevel.ERROR,
                f"Template não encontrado: {project_type.value}"
            )
            return False
        
        try:
            # Converter para Path se necessário
            project_path = Path(project_path)
            
            # Criar diretório do projeto
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Criar estrutura de diretórios
            self._create_directory_structure(project_path, template.structure)
            
            # Criar arquivos de configuração
            self._create_config_files(project_path, template)
            
            # Criar scripts
            self._create_scripts(project_path, template)
            
            # Criar documentação
            self._create_documentation(project_path, template)
            
            from ..utils.advanced_logger import LogLevel
            
            self.logger.log_structured(
                "templates",
                LogLevel.INFO,
                f"Project structure created: {project_path}",
                data={
                    "project_type": project_type.value,
                    "template_name": template.name
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                "project_type": project_type.value,
                "project_path": str(project_path)
            })
            return False
    
    def _create_directory_structure(self, project_path: Path, 
                                  structure: Dict[str, Any]):
        """Cria estrutura de diretórios"""
        for name, content in structure.items():
            dir_path = project_path / name
            dir_path.mkdir(exist_ok=True)
            
            if isinstance(content, dict):
                self._create_directory_structure(dir_path, content)
    
    def _create_config_files(self, project_path: Path, template: ProjectTemplate):
        """Cria arquivos de configuração"""
        for config_file in template.config_files:
            file_path = project_path / config_file
            
            if config_file == "package.json":
                self._create_package_json(file_path, template)
            elif config_file == "requirements.txt":
                self._create_requirements_txt(file_path, template)
            elif config_file == "docker-compose.yml":
                self._create_docker_compose(file_path, template)
            else:
                # Criar arquivo vazio
                file_path.touch()
    
    def _create_package_json(self, file_path: Path, template: ProjectTemplate):
        """Cria package.json"""
        package_data = {
            "name": "project-name",
            "version": "1.0.0",
            "description": template.description,
            "scripts": template.scripts,
            "dependencies": {dep: "latest" for dep in template.dependencies},
            "devDependencies": {
                "typescript": "^4.0.0",
                "jest": "^27.0.0",
                "eslint": "^8.0.0"
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(package_data, f, indent=2)
    
    def _create_requirements_txt(self, file_path: Path, template: ProjectTemplate):
        """Cria requirements.txt"""
        with open(file_path, 'w') as f:
            for dep in template.dependencies:
                f.write(f"{dep}\n")
    
    def _create_docker_compose(self, file_path: Path, template: ProjectTemplate):
        """Cria docker-compose.yml"""
        compose_data = {
            "version": "3.8",
            "services": {
                "app": {
                    "build": ".",
                    "ports": ["3000:3000"],
                    "environment": ["NODE_ENV=development"]
                }
            }
        }
        
        with open(file_path, 'w') as f:
            yaml.dump(compose_data, f, default_flow_style=False)
    
    def _create_scripts(self, project_path: Path, template: ProjectTemplate):
        """Cria scripts"""
        scripts_dir = project_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        for script_name, script_content in template.scripts.items():
            script_file = scripts_dir / f"{script_name}.sh"
            with open(script_file, 'w') as f:
                f.write(f"#!/bin/bash\n{script_content}\n")
            script_file.chmod(0o755)
    
    def _create_documentation(self, project_path: Path, template: ProjectTemplate):
        """Cria documentação"""
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # README.md
        readme_content = f"""# {template.name}

{template.description}

## Estrutura do Projeto

```
{self._format_structure(template.structure)}
```

## Scripts Disponíveis

{self._format_scripts(template.scripts)}

## Validação

{self._format_validation_rules(template.validation_rules)}

## Configuração de Agentes

{self._format_agent_config(template.agent_config)}
"""
        
        with open(docs_dir / "README.md", 'w') as f:
            f.write(readme_content)
    
    def _format_structure(self, structure: Dict[str, Any], indent: int = 0) -> str:
        """Formata estrutura de diretórios"""
        result = ""
        for name, content in structure.items():
            result += "  " * indent + f"├── {name}/\n"
            if isinstance(content, dict):
                result += self._format_structure(content, indent + 1)
        return result
    
    def _format_scripts(self, scripts: Dict[str, str]) -> str:
        """Formata scripts"""
        result = ""
        for name, command in scripts.items():
            result += f"- `{name}`: {command}\n"
        return result
    
    def _format_validation_rules(self, rules: List[str]) -> str:
        """Formata regras de validação"""
        result = ""
        for rule in rules:
            result += f"- {rule}\n"
        return result
    
    def _format_agent_config(self, config: Dict[str, Any]) -> str:
        """Formata configuração de agentes"""
        result = ""
        for key, value in config.items():
            result += f"- **{key}**: {value}\n"
        return result
    
    def validate_template(self, template: ProjectTemplate) -> List[str]:
        """Valida template e retorna erros"""
        errors = []
        
        # Validar campos obrigatórios
        if not template.name:
            errors.append("Nome do template é obrigatório")
        
        if not template.description:
            errors.append("Descrição do template é obrigatória")
        
        if not template.structure:
            errors.append("Estrutura do template é obrigatória")
        
        if not template.dependencies:
            errors.append("Dependências do template são obrigatórias")
        
        # Validar estrutura
        if not self._validate_structure(template.structure):
            errors.append("Estrutura do template é inválida")
        
        return errors
    
    def _validate_structure(self, structure: Dict[str, Any]) -> bool:
        """Valida estrutura de diretórios"""
        if not isinstance(structure, dict):
            return False
        
        for name, content in structure.items():
            if not isinstance(name, str):
                return False
            
            if isinstance(content, dict):
                if not self._validate_structure(content):
                    return False
        
        return True 