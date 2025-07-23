#!/usr/bin/env python3
"""
Agent Orchestrator - Setup
Orquestrador de Agentes de IA para Desenvolvimento de Software
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agent-orchestrator",
    version="1.0.0",
    author="Agent Orchestrator Team",
    author_email="team@agent-orchestrator.dev",
    description="Orquestrador de Agentes de IA para Desenvolvimento de Software",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/agent-orchestrator/agent-orchestrator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent_orchestrator=agent_orchestrator.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, agents, orchestration, development, automation, claude, gemini",
    project_urls={
        "Bug Reports": "https://github.com/agent-orchestrator/agent-orchestrator/issues",
        "Source": "https://github.com/agent-orchestrator/agent-orchestrator",
        "Documentation": "https://agent-orchestrator.readthedocs.io/",
    },
) 