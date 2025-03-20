from django.urls import path

from perspectives.views import PerspectiveCreation, Perspectives


urlpatterns = [
    path(route="perspectives", view=Perspectives.as_view(), name="perspective_list"),
    path(route="perpectives/create", view=PerspectiveCreation.as_view(), name="perspective_create"),
]
