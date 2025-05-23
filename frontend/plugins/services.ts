import { Plugin } from '@nuxt/types'
import { repositories } from './repositories'
import { ExampleApplicationService } from '@/services/application/example/exampleApplicationService'
import { LabelApplicationService } from '@/services/application/label/labelApplicationService'
import { OptionApplicationService } from '@/services/application/option/optionApplicationService'
import { ProjectApplicationService } from '@/services/application/project/projectApplicationService'
import { TagApplicationService } from '@/services/application/tag/tagApplicationService'
import { BoundingBoxApplicationService } from '@/services/application/tasks/boundingBox/boundingBoxApplicationService'
import { SegmentationApplicationService } from '@/services/application/tasks/segmentation/segmentationApplicationService'
import { SequenceLabelingApplicationService } from '@/services/application/tasks/sequenceLabeling/sequenceLabelingApplicationService'
import { UserApplicationService } from '~/services/application/user/userApplicationService'
import { PerspectiveApplicationService } from '~/services/application/perspective/perspectiveApplicationService'
import { QuestionApplicationService, OptionsGroupApplicationService, OptionsQuestionApplicationService, QuestionTypeApplicationService } from '~/services/application/perspective/question/questionApplicationService'
import { AnswerApplicationService } from '~/services/application/perspective/answer/answerApplicationService'
import { VotingConfigurationApplicationService, AnnotationRuleTypeApplicationService, AnnotationRuleApplicationService, AnnotationRuleAnswerApplicationService } from '~/services/application/rules/ruleApplicationService'

export interface Services {
  categoryType: LabelApplicationService
  spanType: LabelApplicationService
  relationType: LabelApplicationService
  project: ProjectApplicationService
  example: ExampleApplicationService
  sequenceLabeling: SequenceLabelingApplicationService
  option: OptionApplicationService
  tag: TagApplicationService
  bbox: BoundingBoxApplicationService
  segmentation: SegmentationApplicationService
  user: UserApplicationService
  perspective: PerspectiveApplicationService
  optionsGroup: OptionsGroupApplicationService
  optionsQuestion: OptionsQuestionApplicationService
  questionType: QuestionTypeApplicationService
  question: QuestionApplicationService
  answer: AnswerApplicationService
  votingConfiguration: VotingConfigurationApplicationService
  annotationRuleType: AnnotationRuleTypeApplicationService
  annotationRule: AnnotationRuleApplicationService
  annotationRuleAnswerService: AnnotationRuleAnswerApplicationService
}

declare module 'vue/types/vue' {
  interface Vue {
    readonly $services: Services
  }
}

const plugin: Plugin = (_, inject) => {
  const services: Services = {
    categoryType: new LabelApplicationService(repositories.categoryType),
    spanType: new LabelApplicationService(repositories.spanType),
    relationType: new LabelApplicationService(repositories.relationType),
    project: new ProjectApplicationService(repositories.project),
    example: new ExampleApplicationService(repositories.example),
    sequenceLabeling: new SequenceLabelingApplicationService(
      repositories.span,
      repositories.relation
    ),
    option: new OptionApplicationService(repositories.option),
    tag: new TagApplicationService(repositories.tag),
    bbox: new BoundingBoxApplicationService(repositories.boundingBox),
    segmentation: new SegmentationApplicationService(repositories.segmentation),
    user: new UserApplicationService(repositories.user),
    perspective: new PerspectiveApplicationService(repositories.perspective),
    optionsGroup: new OptionsGroupApplicationService(repositories.optionsGroup),
    optionsQuestion: new OptionsQuestionApplicationService(repositories.optionsQuestion),
    questionType: new QuestionTypeApplicationService(repositories.questionType),
    question: new QuestionApplicationService(repositories.question),
    answer: new AnswerApplicationService(repositories.answer),
    votingConfiguration: new VotingConfigurationApplicationService(repositories.votingConfiguration),
    annotationRuleType: new AnnotationRuleTypeApplicationService(repositories.annotationRuleType),
    annotationRule: new AnnotationRuleApplicationService(repositories.annotationRule),
    annotationRuleAnswerService: new AnnotationRuleAnswerApplicationService(repositories.annotationRuleAnswer),
  }
  inject('services', services)
}

export default plugin
