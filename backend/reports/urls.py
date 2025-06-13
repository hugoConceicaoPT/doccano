from django.urls import path
from .views import AnnotatorReportView, AnnotatorReportExportView

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
] 