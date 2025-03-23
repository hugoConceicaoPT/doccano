from django.urls import include, path

from .views import Me, UserCreation, UserDeletion, UserEdit , Users

urlpatterns = [
    path(route="me", view=Me.as_view(), name="me"),
    path(route="users", view=Users.as_view(), name="user_list"),
    path(route="users/create", view=UserCreation.as_view(), name="user_create"),
    path(route="users/<int:pk>/delete", view=UserDeletion.as_view(), name="user_delete"),
    path(route="users/<int:pk>/edit", view= UserEdit.as_view(), name="user_edit"),
    path("auth/", include("dj_rest_auth.urls")),
]
