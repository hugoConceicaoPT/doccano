from django.urls import path

from .views.member import MemberDetail, MemberList, MyRole
from .views.perspective import (
    AllPerspectives,
    AnswerCreation,
    Answers,
    PerspectiveCreation,
    PerspectiveDetail,
    Perspectives,
    Questions,
)
from .views.rule import ( 
    AnnotationRules, 
    AnnotationRuleCreation, 
    AnnotationRuleDetail,
    AnnotationRuleAnswersCreation,
    AnnotationRuleAnswersList,
    AnnotationRuleAnswerDetail,
    VotingConfigurations,
    VotingConfigurationCreation,
    UnvotedAnnotationRules,
    )
from .views.project import CloneProject, ProjectDetail, ProjectList
from .views.tag import TagDetail, TagList

urlpatterns = [
    path(route="projects", view=ProjectList.as_view(), name="project_list"),
    path(route="projects/<int:project_id>", view=ProjectDetail.as_view(), name="project_detail"),
    path(route="projects/<int:project_id>/my-role", view=MyRole.as_view(), name="my_role"),
    path(route="projects/<int:project_id>/tags", view=TagList.as_view(), name="tag_list"),
    path(route="projects/<int:project_id>/tags/<int:tag_id>", view=TagDetail.as_view(), name="tag_detail"),
    path(route="projects/<int:project_id>/members", view=MemberList.as_view(), name="member_list"),
    path(route="projects/<int:project_id>/clone", view=CloneProject.as_view(), name="clone_project"),
    path(route="projects/<int:project_id>/members/<int:member_id>", view=MemberDetail.as_view(), name="member_detail"),
    path(route="projects/<int:project_id>/perspectives", view=Perspectives.as_view(), name="perspectives_list"),
    path(route="projects/<int:project_id>/perspectives/create",view=PerspectiveCreation.as_view(),name="perspectives_create",),
    path(route="perspectives/all", view=AllPerspectives.as_view(), name="all_perspectives_list"),
    path(route="answers",view=Answers.as_view(),name="answers_list",),
    path(route="projects/<int:project_id>/perspectives/answers/create",view=AnswerCreation.as_view(),name="answers_create",),
    path(route="projects/<int:project_id>/perspectives/<int:perspective_id>/questions",view=Questions.as_view(),name="questions_list",),
    path(route="projects/<int:project_id>/perspectives/<int:pk>",view=PerspectiveDetail.as_view(),name="perspective_detail",),
    path(route="projects/<int:project_id>/annotation-rules/create",view=AnnotationRuleCreation.as_view(),name="annotation_rule_create",),
    path(route="projects/<int:project_id>/annotation-rules/list",view=AnnotationRules.as_view(),name="annotation_rule_list",),
    path(route="projects/<int:project_id>/annotation-rules/unvoted",view=UnvotedAnnotationRules.as_view(),name="unvoted_annotation_rules",),
    path(route="projects/<int:project_id>/annotation-rules/<int:annotation_rule_id>",view=AnnotationRuleDetail.as_view(),name="annotation_rule_detail",),
    path(route="projects/<int:project_id>/rules/create",view=VotingConfigurationCreation.as_view(),name="voting-configuration",),
    path(route="projects/<int:project_id>/rules/list",view=VotingConfigurations.as_view(),name="voting_configuration_list",),
    path(route="projects/<int:project_id>/annotation-rule-answers/create", view=AnnotationRuleAnswersCreation.as_view(), name="annotation_rule_answers_create"),
    path(route="projects/<int:project_id>/annotation-rule-answers", view=AnnotationRuleAnswersList.as_view(), name="annotation_rule_answers_list"),
    path(route="projects/<int:project_id>/annotation-rule-answers/<int:annotation_rule_answer_id>", view=AnnotationRuleAnswerDetail.as_view(), name="annotation_rule_answer_detail"),
]
