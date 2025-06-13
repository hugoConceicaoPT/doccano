from django.urls import path

from .views import TaskStatus, DatasetReviewView

urlpatterns = [
    path(route="tasks/status/<task_id>", view=TaskStatus.as_view(), name="task_status"),
    path(route="dataset-reviews/", view=DatasetReviewView.as_view(), name="dataset_reviews"),
]
