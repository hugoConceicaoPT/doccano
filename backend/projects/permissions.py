from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Member


class RolePermission(BasePermission):
    UNSAFE_METHODS = ("POST", "PATCH", "DELETE")
    unsafe_methods_check = True
    role_name = ""

    @classmethod
    def get_project_id(cls, request, view):
        return view.kwargs.get("project_id") or request.query_params.get("project_id")

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if self.unsafe_methods_check and request.method in self.UNSAFE_METHODS:
            return request.user.is_superuser

        project_id = self.get_project_id(request, view)
        if not project_id and request.method in SAFE_METHODS:
            return True

        return Member.objects.has_role(project_id, request.user, self.role_name)


class IsProjectAdmin(RolePermission):
    unsafe_methods_check = False
    role_name = settings.ROLE_PROJECT_ADMIN


class IsAnnotatorAndReadOnly(RolePermission):
    unsafe_methods_check = False
    role_name = settings.ROLE_ANNOTATOR


class IsAnnotator(RolePermission):
    unsafe_methods_check = False
    role_name = settings.ROLE_ANNOTATOR


class IsAnnotationApproverAndReadOnly(RolePermission):
    unsafe_methods_check = False
    role_name = settings.ROLE_ANNOTATION_APPROVER


class IsAnnotationApprover(RolePermission):
    unsafe_methods_check = False
    role_name = settings.ROLE_ANNOTATION_APPROVER


class IsAnnotatorForVoting(BasePermission):
    """
    Permissão específica para votação em regras de anotação.
    Permite que apenas anotadores votem nas regras.
    """
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
            
        project_id = view.kwargs.get("project_id")
        if not project_id:
            return False
            
        # Verificar se o usuário é um anotador do projeto
        return Member.objects.has_role(project_id, request.user, settings.ROLE_ANNOTATOR)


IsProjectMember = IsAnnotator | IsAnnotationApprover | IsProjectAdmin  # type: ignore
IsProjectStaffAndReadOnly = IsAnnotatorAndReadOnly | IsAnnotationApproverAndReadOnly  # type: ignore
