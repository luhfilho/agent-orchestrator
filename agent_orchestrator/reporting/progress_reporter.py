"""
Progress Reporter - Agent Orchestrator
Sistema de relatórios de progresso em markdown com métricas
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..models.sprint import Sprint
from ..models.task import Task, TaskResult
from ..utils.advanced_logger import advanced_logger


class ReportFormat(Enum):
    """Formatos de relatório disponíveis"""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    CSV = "csv"


@dataclass
class ProgressMetrics:
    """Métricas de progresso"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    in_progress_tasks: int
    total_points: int
    completed_points: int
    success_rate: float
    average_execution_time: float
    total_execution_time: float
    start_time: datetime
    estimated_completion: Optional[datetime] = None


@dataclass
class QualityMetrics:
    """Métricas de qualidade"""
    code_generated: int
    tests_created: int
    documentation_updated: int
    files_created: int
    errors_fixed: int
    quality_score: float


class ProgressReporter:
    """Sistema de relatórios de progresso"""
    
    def __init__(self, output_dir: Path = Path("./reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.logger = advanced_logger
    
    def generate_sprint_report(self, sprint: Sprint, task_results: List[TaskResult],
                              format: ReportFormat = ReportFormat.MARKDOWN) -> Path:
        """
        Gera relatório de progresso do sprint
        
        Args:
            sprint: Sprint sendo executado
            task_results: Resultados das tasks
            format: Formato do relatório
            
        Returns:
            Path: Caminho do arquivo gerado
        """
        # Calcular métricas
        metrics = self._calculate_progress_metrics(sprint, task_results)
        quality_metrics = self._calculate_quality_metrics(task_results)
        
        # Gerar relatório no formato especificado
        if format == ReportFormat.MARKDOWN:
            return self._generate_markdown_report(sprint, metrics, quality_metrics, task_results)
        elif format == ReportFormat.JSON:
            return self._generate_json_report(sprint, metrics, quality_metrics, task_results)
        elif format == ReportFormat.HTML:
            return self._generate_html_report(sprint, metrics, quality_metrics, task_results)
        elif format == ReportFormat.CSV:
            return self._generate_csv_report(sprint, metrics, quality_metrics, task_results)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def _calculate_progress_metrics(self, sprint: Sprint, 
                                   task_results: List[TaskResult]) -> ProgressMetrics:
        """Calcula métricas de progresso"""
        total_tasks = len(sprint.user_stories)
        completed_tasks = len([r for r in task_results if r.success])
        failed_tasks = len([r for r in task_results if not r.success])
        in_progress_tasks = total_tasks - completed_tasks - failed_tasks
        
        total_points = sum(s.story_points for s in sprint.user_stories)
        completed_points = sum(
            s.story_points for s, r in zip(sprint.user_stories, task_results) 
            if r.success
        ) if task_results else 0
        
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        total_execution_time = sum(r.execution_time for r in task_results)
        average_execution_time = total_execution_time / len(task_results) if task_results else 0.0
        
        # Estimar tempo de conclusão
        estimated_completion = None
        if completed_tasks > 0 and in_progress_tasks > 0:
            avg_time_per_task = total_execution_time / completed_tasks
            remaining_time = avg_time_per_task * in_progress_tasks
            estimated_completion = datetime.now() + timedelta(seconds=remaining_time)
        
        return ProgressMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            in_progress_tasks=in_progress_tasks,
            total_points=total_points,
            completed_points=completed_points,
            success_rate=success_rate,
            average_execution_time=average_execution_time,
            total_execution_time=total_execution_time,
            start_time=sprint.start_date,
            estimated_completion=estimated_completion
        )
    
    def _calculate_quality_metrics(self, task_results: List[TaskResult]) -> QualityMetrics:
        """Calcula métricas de qualidade"""
        code_generated = sum(1 for r in task_results if r.data and r.data.get("code_generated", False))
        tests_created = sum(1 for r in task_results if r.data and r.data.get("tests_created", False))
        documentation_updated = sum(1 for r in task_results if r.data and r.data.get("documentation", False))
        files_created = sum(len(r.data.get("files_created", [])) for r in task_results if r.data)
        errors_fixed = sum(1 for r in task_results if r.success and r.data and r.data.get("errors_fixed", 0))
        
        # Calcular score de qualidade (0-100)
        quality_factors = [
            code_generated / len(task_results) * 30 if task_results else 0,
            tests_created / len(task_results) * 25 if task_results else 0,
            documentation_updated / len(task_results) * 20 if task_results else 0,
            min(files_created / len(task_results), 1.0) * 15 if task_results else 0,
            errors_fixed / len(task_results) * 10 if task_results else 0
        ]
        quality_score = sum(quality_factors)
        
        return QualityMetrics(
            code_generated=code_generated,
            tests_created=tests_created,
            documentation_updated=documentation_updated,
            files_created=files_created,
            errors_fixed=errors_fixed,
            quality_score=quality_score
        )
    
    def _generate_markdown_report(self, sprint: Sprint, metrics: ProgressMetrics,
                                 quality_metrics: QualityMetrics,
                                 task_results: List[TaskResult]) -> Path:
        """Gera relatório em formato Markdown"""
        report_file = self.output_dir / f"sprint_report_{sprint.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write(f"# Relatório de Progresso - Sprint {sprint.id}\n\n")
            f.write(f"**Data do Relatório:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumo executivo
            f.write("## 📊 Resumo Executivo\n\n")
            f.write(f"- **Sprint:** {sprint.name}\n")
            f.write(f"- **Status:** {sprint.status}\n")
            f.write(f"- **Progresso:** {metrics.completed_tasks}/{metrics.total_tasks} tasks ({metrics.success_rate:.1f}%)\n")
            points_percentage = (metrics.completed_points/metrics.total_points*100) if metrics.total_points > 0 else 0.0
            f.write(f"- **Pontos:** {metrics.completed_points}/{metrics.total_points} ({points_percentage:.1f}%)\n")
            f.write(f"- **Taxa de Sucesso:** {metrics.success_rate:.1f}%\n")
            f.write(f"- **Tempo Total:** {metrics.total_execution_time:.2f}s\n\n")
            
            # Métricas de progresso
            f.write("## 📈 Métricas de Progresso\n\n")
            f.write("| Métrica | Valor |\n")
            f.write("|---------|-------|\n")
            f.write(f"| Total de Tasks | {metrics.total_tasks} |\n")
            f.write(f"| Tasks Concluídas | {metrics.completed_tasks} |\n")
            f.write(f"| Tasks Falharam | {metrics.failed_tasks} |\n")
            f.write(f"| Tasks em Progresso | {metrics.in_progress_tasks} |\n")
            f.write(f"| Total de Pontos | {metrics.total_points} |\n")
            f.write(f"| Pontos Concluídos | {metrics.completed_points} |\n")
            f.write(f"| Taxa de Sucesso | {metrics.success_rate:.1f}% |\n")
            f.write(f"| Tempo Médio por Task | {metrics.average_execution_time:.2f}s |\n")
            f.write(f"| Tempo Total | {metrics.total_execution_time:.2f}s |\n")
            
            if metrics.estimated_completion:
                f.write(f"| Estimativa de Conclusão | {metrics.estimated_completion.strftime('%Y-%m-%d %H:%M:%S')} |\n")
            
            f.write("\n")
            
            # Métricas de qualidade
            f.write("## 🎯 Métricas de Qualidade\n\n")
            f.write("| Métrica | Valor |\n")
            f.write("|---------|-------|\n")
            f.write(f"| Código Gerado | {quality_metrics.code_generated} |\n")
            f.write(f"| Testes Criados | {quality_metrics.tests_created} |\n")
            f.write(f"| Documentação Atualizada | {quality_metrics.documentation_updated} |\n")
            f.write(f"| Arquivos Criados | {quality_metrics.files_created} |\n")
            f.write(f"| Erros Corrigidos | {quality_metrics.errors_fixed} |\n")
            f.write(f"| Score de Qualidade | {quality_metrics.quality_score:.1f}/100 |\n\n")
            
            # Detalhes das tasks
            f.write("## ⚡ Detalhes das Tasks\n\n")
            f.write("| Task | Status | Agente | Tempo | Pontos |\n")
            f.write("|------|--------|--------|-------|--------|\n")
            
            for i, (story, result) in enumerate(zip(sprint.user_stories, task_results)):
                status = "✅ Sucesso" if result.success else "❌ Falha"
                f.write(f"| {story.id} | {status} | {result.agent_used} | {result.execution_time:.2f}s | {story.story_points} |\n")
            
            f.write("\n")
            
            # Gráfico de progresso (ASCII)
            f.write("## 📊 Gráfico de Progresso\n\n")
            progress_bar = self._generate_ascii_progress_bar(metrics.completed_tasks, metrics.total_tasks)
            f.write(f"```\n{progress_bar}\n```\n\n")
            
            # Recomendações
            f.write("## 💡 Recomendações\n\n")
            recommendations = self._generate_recommendations(metrics, quality_metrics)
            for rec in recommendations:
                f.write(f"- {rec}\n")
            
            f.write("\n")
            
            # Logs de execução
            f.write("## 📝 Logs de Execução\n\n")
            f.write("```json\n")
            f.write(json.dumps([r.dict() for r in task_results], indent=2, default=str))
            f.write("\n```\n")
        
        return report_file
    
    def _generate_json_report(self, sprint: Sprint, metrics: ProgressMetrics,
                             quality_metrics: QualityMetrics,
                             task_results: List[TaskResult]) -> Path:
        """Gera relatório em formato JSON"""
        report_file = self.output_dir / f"sprint_report_{sprint.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "sprint": {
                "id": sprint.id,
                "name": sprint.name,
                "status": sprint.status,
                "start_date": sprint.start_date.isoformat(),
                "end_date": sprint.end_date.isoformat()
            },
            "metrics": asdict(metrics),
            "quality_metrics": asdict(quality_metrics),
            "task_results": [r.dict() for r in task_results],
            "generated_at": datetime.now().isoformat()
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return report_file
    
    def _generate_html_report(self, sprint: Sprint, metrics: ProgressMetrics,
                             quality_metrics: QualityMetrics,
                             task_results: List[TaskResult]) -> Path:
        """Gera relatório em formato HTML"""
        report_file = self.output_dir / f"sprint_report_{sprint.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Relatório Sprint {sprint.id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .metric {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Relatório de Progresso - Sprint {sprint.id}</h1>
    <p><strong>Data:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Resumo</h2>
    <div class="metric">
        <p><strong>Progresso:</strong> {metrics.completed_tasks}/{metrics.total_tasks} tasks ({metrics.success_rate:.1f}%)</p>
        <p><strong>Taxa de Sucesso:</strong> {metrics.success_rate:.1f}%</p>
        <p><strong>Tempo Total:</strong> {metrics.total_execution_time:.2f}s</p>
    </div>
    
    <h2>Tasks</h2>
    <table>
        <tr><th>Task</th><th>Status</th><th>Agente</th><th>Tempo</th></tr>
"""
        
        for story, result in zip(sprint.user_stories, task_results):
            status_class = "success" if result.success else "error"
            status_text = "✅ Sucesso" if result.success else "❌ Falha"
            html_content += f"""
        <tr>
            <td>{story.id}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result.agent_used}</td>
            <td>{result.execution_time:.2f}s</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file
    
    def _generate_csv_report(self, sprint: Sprint, metrics: ProgressMetrics,
                            quality_metrics: QualityMetrics,
                            task_results: List[TaskResult]) -> Path:
        """Gera relatório em formato CSV"""
        report_file = self.output_dir / f"sprint_report_{sprint.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("Task ID,Status,Agente,Tempo Execução,Pontos,Sucesso\n")
            
            # Dados das tasks
            for story, result in zip(sprint.user_stories, task_results):
                status = "Sucesso" if result.success else "Falha"
                f.write(f"{story.id},{status},{result.agent_used},{result.execution_time:.2f},{story.story_points},{result.success}\n")
        
        return report_file
    
    def _generate_ascii_progress_bar(self, completed: int, total: int, width: int = 50) -> str:
        """Gera barra de progresso ASCII"""
        if total == 0:
            return "[" + " " * width + "] 0%"
        
        percentage = completed / total
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage*100:.1f}%"
    
    def _generate_recommendations(self, metrics: ProgressMetrics, 
                                 quality_metrics: QualityMetrics) -> List[str]:
        """Gera recomendações baseadas nas métricas"""
        recommendations = []
        
        if metrics.success_rate < 80:
            recommendations.append("Taxa de sucesso baixa - revisar configuração dos agentes")
        
        if metrics.average_execution_time > 30:
            recommendations.append("Tempo de execução alto - considerar otimizações")
        
        if quality_metrics.quality_score < 70:
            recommendations.append("Score de qualidade baixo - melhorar critérios de aceite")
        
        if quality_metrics.tests_created < metrics.completed_tasks * 0.5:
            recommendations.append("Poucos testes criados - priorizar cobertura de testes")
        
        if quality_metrics.documentation_updated < metrics.completed_tasks * 0.3:
            recommendations.append("Documentação insuficiente - melhorar documentação")
        
        if not recommendations:
            recommendations.append("Sprint executado com sucesso - manter padrões atuais")
        
        return recommendations
    
    def export_report(self, report_path: Path, format: ReportFormat) -> Path:
        """Exporta relatório para formato específico"""
        if format == ReportFormat.MARKDOWN:
            return report_path
        elif format == ReportFormat.JSON:
            return self._convert_to_json(report_path)
        elif format == ReportFormat.HTML:
            return self._convert_to_html(report_path)
        elif format == ReportFormat.CSV:
            return self._convert_to_csv(report_path)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def _convert_to_json(self, report_path: Path) -> Path:
        """Converte relatório para JSON"""
        # Implementação básica - em produção seria mais robusta
        json_path = report_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({"report_path": str(report_path)}, f)
        return json_path
    
    def _convert_to_html(self, report_path: Path) -> Path:
        """Converte relatório para HTML"""
        html_path = report_path.with_suffix('.html')
        with open(html_path, 'w') as f:
            f.write(f"<html><body><h1>Relatório</h1><p>Ver: {report_path}</p></body></html>")
        return html_path
    
    def _convert_to_csv(self, report_path: Path) -> Path:
        """Converte relatório para CSV"""
        csv_path = report_path.with_suffix('.csv')
        with open(csv_path, 'w') as f:
            f.write(f"report_path\n{report_path}")
        return csv_path 