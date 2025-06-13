from django.urls import path
from .views import (
    AnnotatorReportView, 
    AnnotatorReportExportView,
    # Novas views
    AnnotationReportView,
    AnnotationReportExportView
)

urlpatterns = [
    path(
        route="annotators/",
        view=AnnotatorReportView.as_view(),
        name="annotator_report"
    ),
    path(
        route="annotators/export/",
        view=AnnotatorReportExportView.as_view(),
        name="annotator_report_export"
    ),
    # Adicionar versão sem trailing slash para compatibilidade
    path(
        route="annotators/export",
        view=AnnotatorReportExportView.as_view(),
        name="annotator_report_export_no_slash"
    ),
    
    # Novos endpoints para relatórios de anotações
    path(
        route="annotations/",
        view=AnnotationReportView.as_view(),
        name="annotation_report"
    ),
    path(
        route="annotations/export/",
        view=AnnotationReportExportView.as_view(),
        name="annotation_report_export"
    ),
    # Adicionar versão sem trailing slash para compatibilidade
    path(
        route="annotations/export",
        view=AnnotationReportExportView.as_view(),
        name="annotation_report_export_no_slash"
    ),
] 