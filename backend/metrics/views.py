import abc
import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from examples.models import Example, ExampleState
from label_types.models import CategoryType, LabelType, RelationType, SpanType
from labels.models import Category, Label, Relation, Span
from projects.models import Member, Project
from projects.permissions import IsProjectAdmin, IsProjectStaffAndReadOnly

logger = logging.getLogger(__name__)


class ProgressAPI(APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    def get(self, request, *args, **kwargs):
        examples = Example.objects.filter(project=self.kwargs["project_id"]).values("id")
        total = examples.count()
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        if project.collaborative_annotation:
            complete = ExampleState.objects.count_done(examples)
        else:
            complete = ExampleState.objects.count_done(examples, user=self.request.user)
        data = {"total": total, "remaining": total - complete, "complete": complete}
        return Response(data=data, status=status.HTTP_200_OK)


class MemberProgressAPI(APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]

    def get(self, request, *args, **kwargs):
        examples = Example.objects.filter(project=self.kwargs["project_id"]).values("id")
        members = Member.objects.filter(project=self.kwargs["project_id"])
        data = ExampleState.objects.measure_member_progress(examples, members)
        return Response(data=data, status=status.HTTP_200_OK)


class LabelDistribution(abc.ABC, APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]
    model = Label
    label_type = LabelType

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]
        logger.info(f"Recebida chamada para {self.__class__.__name__}, project_id: {project_id}")
        
        try:
            # Verificar se o projeto existe
            project = get_object_or_404(Project, pk=project_id)
            logger.info(f"Projeto encontrado: {project.name}")
            
            labels = self.label_type.objects.filter(project=project_id)
            examples = Example.objects.filter(project=project_id).values("id")
            members = Member.objects.filter(project=project_id)
            
            logger.info(f"Encontrados: {labels.count()} labels, {examples.count()} examples, {members.count()} members")
            
            # Verificar se há dados para processar
            if not labels.exists():
                logger.info("Nenhum label encontrado, retornando dados vazios")
                return Response(data={}, status=status.HTTP_200_OK)
            
            if not members.exists():
                logger.info("Nenhum membro encontrado, retornando dados vazios")
                return Response(data={}, status=status.HTTP_200_OK)
            
            data = self.model.objects.calc_label_distribution(examples, members, labels)
            logger.info(f"Dados calculados com sucesso para {len(data)} utilizadores")
            
            return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erro em {self.__class__.__name__}: {str(e)}", exc_info=True)
            # Retornar dados vazios em vez de erro 500
            return Response(data={}, status=status.HTTP_200_OK)


class LabelPercentage(abc.ABC, APIView):
    permission_classes = [IsAuthenticated & (IsProjectAdmin | IsProjectStaffAndReadOnly)]
    model = Label
    label_type = LabelType

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs["project_id"]
        logger.info(f"Recebida chamada para {self.__class__.__name__}, project_id: {project_id}")
        
        try:
            # Verificar se o projeto existe
            project = get_object_or_404(Project, pk=project_id)
            logger.info(f"Projeto encontrado: {project.name}")
            
            labels = self.label_type.objects.filter(project=project_id)
            examples = list(Example.objects.filter(project=project_id).values_list("id", flat=True))
            
            logger.info(f"Encontrados: {labels.count()} labels, {len(examples)} examples")
            
            # Verificar se há dados para processar
            if not labels.exists():
                logger.info("Nenhum label encontrado, retornando dados vazios")
                return Response(data={}, status=status.HTTP_200_OK)
            
            if not examples:
                logger.info("Nenhum example encontrado, retornando dados vazios")
                return Response(data={}, status=status.HTTP_200_OK)
            
            data = self.model.objects.get_label_percentage(examples, labels)
            logger.info(f"Dados calculados com sucesso para {len(data)} examples")
            
            return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erro em {self.__class__.__name__}: {str(e)}", exc_info=True)
            # Retornar dados vazios em vez de erro 500
            return Response(data={}, status=status.HTTP_200_OK)

class CategoryTypeDistribution(LabelDistribution):
    model = Category
    label_type = CategoryType


class SpanTypeDistribution(LabelDistribution):
    model = Span
    label_type = SpanType


class RelationTypeDistribution(LabelDistribution):
    model = Relation
    label_type = RelationType

class CategoryTypePercentage(LabelPercentage):
    model = Category
    label_type = CategoryType


class SpanTypePercentage(LabelPercentage):
    model = Span
    label_type = SpanType


class RelationTypePercentage(LabelPercentage):
    model = Relation
    label_type = RelationType
