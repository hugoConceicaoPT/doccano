from django.urls import path

from .views import TaskStatus, DatasetReviewView, DatasetReviewListView

urlpatterns = [
    path(route="tasks/status/<task_id>", view=TaskStatus.as_view(), name="task_status"),
    path(route="dataset-reviews/", view=DatasetReviewView.as_view(), name="dataset_reviews"),
    path(route="dataset-reviews/list/", view=DatasetReviewListView.as_view(), name="dataset_reviews_list"),
]
