from django.urls import path

from statistics.views import PerspectiveAnswerDistribution

urlpatterns = [
    path(route="perspective-answer-distribution", view=PerspectiveAnswerDistribution.as_view(), name="perspective_answer_distribution"),
]