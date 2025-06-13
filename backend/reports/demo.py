#!/usr/bin/env python3
"""
Script de demonstração da funcionalidade de relatório de anotadores
Este script mostra como a API funcionaria sem precisar executar o Django
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


class MockAnnotatorReportService:
    """Versão mock do AnnotatorReportService para demonstração"""
    
    @staticmethod
    def get_report(
        project_ids: List[int],
        user_ids: List[int] = None,
        date_from: datetime = None,
        date_to: datetime = None,
        label_ids: List[int] = None,
        task_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Simula a geração de um relatório sobre anotadores
        """
        
        # Dados mock para demonstração
        mock_data = [
            {
                "annotator_id": 1,
                "annotator_name": "Maria Silva",
                "annotator_username": "maria.silva",
                "total_annotations": 1250,
                "categories_count": 800,
                "spans_count": 350,
                "texts_count": 100,
                "avg_time_per_annotation": 45.2,
                "first_annotation_date": datetime.now() - timedelta(days=30),
                "last_annotation_date": datetime.now() - timedelta(hours=2),
                "label_breakdown": {
                    "PESSOA": 320,
                    "ORGANIZAÇÃO": 280,
                    "LOCAL": 200,
                    "PRODUTO": 150,
                    "EVENTO": 100,
                    "OUTROS": 200
                }
            },
            {
                "annotator_id": 2,
                "annotator_name": "João Santos",
                "annotator_username": "joao.santos",
                "total_annotations": 980,
                "categories_count": 600,
                "spans_count": 280,
                "texts_count": 100,
                "avg_time_per_annotation": 52.8,
                "first_annotation_date": datetime.now() - timedelta(days=25),
                "last_annotation_date": datetime.now() - timedelta(hours=5),
                "label_breakdown": {
                    "PESSOA": 250,
                    "ORGANIZAÇÃO": 220,
                    "LOCAL": 180,
                    "PRODUTO": 130,
                    "EVENTO": 80,
                    "OUTROS": 120
                }
            },
            {
                "annotator_id": 3,
                "annotator_name": "Ana Costa",
                "annotator_username": "ana.costa",
                "total_annotations": 750,
                "categories_count": 450,
                "spans_count": 200,
                "texts_count": 100,
                "avg_time_per_annotation": 38.5,
                "first_annotation_date": datetime.now() - timedelta(days=20),
                "last_annotation_date": datetime.now() - timedelta(hours=1),
                "label_breakdown": {
                    "PESSOA": 180,
                    "ORGANIZAÇÃO": 160,
                    "LOCAL": 140,
                    "PRODUTO": 100,
                    "EVENTO": 70,
                    "OUTROS": 100
                }
            }
        ]
        
        # Aplicar filtros se especificados
        if user_ids:
            mock_data = [item for item in mock_data if item["annotator_id"] in user_ids]
        
        # Calcular resumo
        summary = {
            "total_annotators": len(mock_data),
            "total_annotations": sum(item["total_annotations"] for item in mock_data),
            "total_categories": sum(item["categories_count"] for item in mock_data),
            "total_spans": sum(item["spans_count"] for item in mock_data),
            "total_texts": sum(item["texts_count"] for item in mock_data),
            "date_range_from": date_from,
            "date_range_to": date_to
        }
        
        return {
            "summary": summary,
            "data": mock_data
        }


def demo_basic_report():
    """Demonstração de relatório básico"""
    print("=== DEMONSTRAÇÃO: Relatório Básico de Anotadores ===\n")
    
    # Simular chamada à API
    report = MockAnnotatorReportService.get_report(project_ids=[1, 2])
    
    # Mostrar resumo
    print("📊 RESUMO GERAL:")
    print(f"   • Total de anotadores: {report['summary']['total_annotators']}")
    print(f"   • Total de anotações: {report['summary']['total_annotations']}")
    print(f"   • Total de categorias: {report['summary']['total_categories']}")
    print(f"   • Total de spans: {report['summary']['total_spans']}")
    print(f"   • Total de textos: {report['summary']['total_texts']}")
    print()
    
    # Mostrar dados por anotador
    print("👥 DADOS POR ANOTADOR:")
    for i, annotator in enumerate(report['data'], 1):
        print(f"\n   {i}. {annotator['annotator_name']} (@{annotator['annotator_username']})")
        print(f"      • Total de anotações: {annotator['total_annotations']}")
        print(f"      • Categorias: {annotator['categories_count']}")
        print(f"      • Spans: {annotator['spans_count']}")
        print(f"      • Textos: {annotator['texts_count']}")
        print(f"      • Tempo médio por anotação: {annotator['avg_time_per_annotation']:.1f}s")
        print(f"      • Primeira anotação: {annotator['first_annotation_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"      • Última anotação: {annotator['last_annotation_date'].strftime('%Y-%m-%d %H:%M')}")
        
        # Top 3 rótulos mais usados
        top_labels = sorted(annotator['label_breakdown'].items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"      • Top 3 rótulos: {', '.join([f'{label}({count})' for label, count in top_labels])}")


def demo_filtered_report():
    """Demonstração de relatório com filtros"""
    print("\n\n=== DEMONSTRAÇÃO: Relatório com Filtros ===\n")
    
    # Simular chamada à API com filtros
    report = MockAnnotatorReportService.get_report(
        project_ids=[1],
        user_ids=[1, 3],  # Apenas Maria e Ana
        date_from=datetime.now() - timedelta(days=30),
        date_to=datetime.now()
    )
    
    print("🔍 FILTROS APLICADOS:")
    print("   • Projetos: [1]")
    print("   • Utilizadores: [1, 3] (Maria Silva, Ana Costa)")
    print("   • Período: Últimos 30 dias")
    print()
    
    print("📊 RESUMO FILTRADO:")
    print(f"   • Total de anotadores: {report['summary']['total_annotators']}")
    print(f"   • Total de anotações: {report['summary']['total_annotations']}")
    print()
    
    print("👥 ANOTADORES FILTRADOS:")
    for annotator in report['data']:
        print(f"   • {annotator['annotator_name']}: {annotator['total_annotations']} anotações")


def demo_api_usage():
    """Demonstração de como usar a API"""
    print("\n\n=== DEMONSTRAÇÃO: Como Usar a API ===\n")
    
    print("🌐 ENDPOINTS DISPONÍVEIS:")
    print("   1. GET /v1/reports/annotators/")
    print("      • Gerar relatório em formato JSON")
    print("   2. GET /v1/reports/annotators/export/")
    print("      • Exportar relatório em formato CSV")
    print()
    
    print("📝 PARÂMETROS DE FILTRO:")
    print("   • project_ids (obrigatório): Lista de IDs dos projetos")
    print("   • user_ids (opcional): Lista de IDs dos utilizadores")
    print("   • date_from (opcional): Data de início (ISO format)")
    print("   • date_to (opcional): Data de fim (ISO format)")
    print("   • label_ids (opcional): Lista de IDs dos rótulos")
    print("   • task_types (opcional): Lista de tipos de tarefa")
    print()
    
    print("🔧 EXEMPLOS DE CHAMADAS:")
    print("   # Relatório básico")
    print("   GET /v1/reports/annotators/?project_ids=1,2")
    print()
    print("   # Relatório filtrado por utilizador e data")
    print("   GET /v1/reports/annotators/?project_ids=1&user_ids=1,3&date_from=2024-01-01T00:00:00Z")
    print()
    print("   # Exportar para CSV")
    print("   GET /v1/reports/annotators/export/?project_ids=1,2")
    print()
    
    print("🔐 PERMISSÕES NECESSÁRIAS:")
    print("   • Utilizador autenticado")
    print("   • Role de Project Admin ou Annotation Approver nos projetos especificados")


def demo_csv_export():
    """Demonstração do formato de exportação CSV"""
    print("\n\n=== DEMONSTRAÇÃO: Formato de Exportação CSV ===\n")
    
    report = MockAnnotatorReportService.get_report(project_ids=[1])
    
    print("📄 ESTRUTURA DO CSV:")
    print("ID Anotador,Nome Utilizador,Nome Completo,Total Anotações,Categorias,Spans,Textos,Primeira Anotação,Última Anotação,Breakdown Rótulos")
    
    for annotator in report['data'][:2]:  # Mostrar apenas 2 para exemplo
        label_breakdown = '; '.join([f"{label}: {count}" for label, count in annotator['label_breakdown'].items()])
        print(f"{annotator['annotator_id']},{annotator['annotator_username']},{annotator['annotator_name']},{annotator['total_annotations']},{annotator['categories_count']},{annotator['spans_count']},{annotator['texts_count']},{annotator['first_annotation_date'].strftime('%Y-%m-%d %H:%M:%S')},{annotator['last_annotation_date'].strftime('%Y-%m-%d %H:%M:%S')},\"{label_breakdown}\"")
    
    print("\n📊 RESUMO NO FINAL DO CSV:")
    print("RESUMO")
    print(f"Total Anotadores,{report['summary']['total_annotators']}")
    print(f"Total Anotações,{report['summary']['total_annotations']}")
    print(f"Total Categorias,{report['summary']['total_categories']}")


if __name__ == "__main__":
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE RELATÓRIOS DE ANOTADORES")
    print("=" * 60)
    
    demo_basic_report()
    demo_filtered_report()
    demo_api_usage()
    demo_csv_export()
    
    print("\n\n✅ IMPLEMENTAÇÃO CONCLUÍDA!")
    print("\nFuncionalidades implementadas:")
    print("• ✅ Service layer para lógica de negócio")
    print("• ✅ Serializers para validação de entrada e saída")
    print("• ✅ Views com permissões adequadas")
    print("• ✅ Endpoints para JSON e exportação CSV")
    print("• ✅ Filtros por projeto, utilizador, data, rótulos")
    print("• ✅ Breakdown detalhado por tipo de anotação")
    print("• ✅ Documentação Swagger automática")
    print("\nPróximos passos:")
    print("• Instalar dependências (poetry install)")
    print("• Executar migrações (python manage.py migrate)")
    print("• Testar endpoints via Swagger UI (/swagger/)")
    print("• Implementar interface frontend (opcional)") 