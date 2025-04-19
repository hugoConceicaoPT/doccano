from django.urls import path

from .views.member import MemberDetail, MemberList, MyRole
from .views.perspective import (
    AnswerCreation,
    Answers,
    OptionsGroupDetail,
    OptionsGroups,
    OptionsGroupsCreation,
    OptionsQuestionCreation,
    PerspectiveCreation,
    PerspectiveDetail,
    Perspectives,
    Questions,
    QuestionsTypeCreation,
    QuestionsTypeDetail,
    OptionsQuestion,
)
from .views.rule import ( 
    AnnotationRules, 
    AnnotationRuleCreation, 
    AnnotationRuleDetail,
    AnnotationRuleTypes,
    AnnotationRuleTypeCreation,
    AnnotationRuleTypeDetail,
    AnnotationRuleAnswersCreation,
    AnnotationRuleAnswerDetail,
    VotingConfigurations,
    VotingConfigurationCreation,
    VotingConfigurationDetail,
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
    path(route="answers",view=Answers.as_view(),name="answers_list",),
    path(route="projects/<int:project_id>/perspectives/answers/create",view=AnswerCreation.as_view(),name="answers_create",),
    path(route="projects/<int:project_id>/perspectives/<int:perspective_id>/questions",view=Questions.as_view(),name="questions_list",),
    path(route="projects/<int:project_id>/options-questions",view=OptionsQuestion.as_view(),name="option_questions_list",),
    path(route="projects/<int:project_id>/perspectives/<int:pk>",view=PerspectiveDetail.as_view(),name="perspective_detail",),
    path(route="projects/<int:project_id>/options-group/create",view=OptionsGroupsCreation.as_view(),name="options_group_create",),
    path(route="projects/<int:project_id>/options-group",view=OptionsGroups.as_view(),name="options_group_list",),
    path(route="projects/<int:project_id>/options-group/<str:group_name>",view=OptionsGroupDetail.as_view(),name="options_group_detail",),
    path(route="projects/<int:project_id>/options-question/create",view=OptionsQuestionCreation.as_view(),name="options_question_create",),
    path(route="projects/<int:project_id>/question-type/create",view=QuestionsTypeCreation.as_view(),name="options_question_create",),
    path(route="projects/<int:project_id>/question-type/<int:question_type_id>",view=QuestionsTypeDetail.as_view(),name="question_type_detail",),
    path(route="projects/<int:project_id>/annotation-rules/create",view=AnnotationRuleCreation.as_view(),name="annotation_rule_create",),
    path(route="projects/<int:project_id>/annotation-rules/list",view=AnnotationRules.as_view(),name="annotation_rule_list",),
    path(route="projects/<int:project_id>/annotation-rules/<int:annotation_rule_id>",view=AnnotationRuleDetail.as_view(),name="annotation_rule_detail",),
    path(route="projects/<int:project_id>/annotation-rule-types",view=AnnotationRuleTypes.as_view(),name="annotation_rule_type_list",),
    path(route="projects/<int:project_id>/rules/create",view=VotingConfigurationCreation.as_view(),name="voting-configuration",),
    path(route="projects/<int:project_id>/rules/list",view=VotingConfigurations.as_view(),name="voting_configuration_list",),
]
