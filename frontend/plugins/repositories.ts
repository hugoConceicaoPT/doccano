import { Plugin } from '@nuxt/types'
import { APIAssignmentRepository } from '@/repositories/example/apiAssignmentRepository'
import { APIAuthRepository } from '@/repositories/auth/apiAuthRepository'
import { APIConfigRepository } from '@/repositories/autoLabeling/config/apiConfigRepository'
import { APITemplateRepository } from '@/repositories/autoLabeling/template/apiTemplateRepository'
import { APITaskStatusRepository } from '@/repositories/celery/apiTaskStatusRepository'
import { APICommentRepository } from '@/repositories/comment/apiCommentRepository'
import { APIDownloadFormatRepository } from '@/repositories/download/apiDownloadFormatRepository'
import { APIDownloadRepository } from '@/repositories/download/apiDownloadRepository'
import { APIExampleRepository } from '@/repositories/example/apiDocumentRepository'
import { APILabelRepository } from '@/repositories/label/apiLabelRepository'
import { APIMemberRepository } from '@/repositories/member/apiMemberRepository'
import { APIMetricsRepository } from '@/repositories/metrics/apiMetricsRepository'
import { LocalStorageOptionRepository } from '@/repositories/option/apiOptionRepository'
import { APIProjectRepository } from '@/repositories/project/apiProjectRepository'
import { APIRoleRepository } from '@/repositories/role/apiRoleRepository'
import { APITagRepository } from '@/repositories/tag/apiTagRepository'
import { APIBoundingBoxRepository } from '@/repositories/tasks/apiBoundingBoxRepository'
import { APICategoryRepository } from '@/repositories/tasks/apiCategoryRepository'
import { APIRelationRepository } from '@/repositories/tasks/apiRelationRepository'
import { APISpanRepository } from '@/repositories/tasks/apiSpanRepository'
import { APITextLabelRepository } from '@/repositories/tasks/apiTextLabelRepository'
import { APICatalogRepository } from '@/repositories/upload/apiCatalogRepository'
import { APIParseRepository } from '@/repositories/upload/apiParseRepository'
import { APIUserRepository } from '@/repositories/user/apiUserRepository'
import { APISegmentationRepository } from '~/repositories/tasks/apiSegmentationRepository'
import { APIPerspectiveRepository } from '~/repositories/perspective/apiPerspectiveRepository'
import { APIQuestionRepository } from '~/repositories/perspective/question/apiQuestionRepository'
import { APIOptionsGroupRepository } from '~/repositories/perspective/question/apiOptionsGroupRepository'
import { APIOptionsQuestionRepository } from '~/repositories/perspective/question/apiOptionsQuestionReposity'
import { APIQuestionTypeRepository } from '~/repositories/perspective/question/apiQuestionTypeReposity'
import { APIAnswerRepository } from '~/repositories/perspective/answer/apiAnswerRepository'
import { APIVotingConfigurationRepository, APIAnnotationRuleTypeRepository, APIAnnotationRuleRepository, APIAnnotationRuleAnswerRepository } from '~/repositories/rules/apiRuleRepository'
import { APIStatisticsRepository } from '~/repositories/statistics/apiStatisticsRepository'

export interface Repositories {
  // User
  auth: APIAuthRepository
  user: APIUserRepository

  // Project
  project: APIProjectRepository
  member: APIMemberRepository
  role: APIRoleRepository
  tag: APITagRepository
  perspective: APIPerspectiveRepository
  question: APIQuestionRepository
  optionsGroup: APIOptionsGroupRepository
  optionsQuestion: APIOptionsQuestionRepository
  questionType: APIQuestionTypeRepository
  answer: APIAnswerRepository 
  votingConfiguration: APIVotingConfigurationRepository
  annotationRuleType: APIAnnotationRuleTypeRepository
  annotationRule: APIAnnotationRuleRepository
  annotationRuleAnswer: APIAnnotationRuleAnswerRepository

  // Example
  example: APIExampleRepository
  comment: APICommentRepository
  taskStatus: APITaskStatusRepository
  metrics: APIMetricsRepository
  statistics: APIStatisticsRepository
  option: LocalStorageOptionRepository
  assignment: APIAssignmentRepository

  // Auto Labeling
  config: APIConfigRepository
  template: APITemplateRepository

  // Upload
  catalog: APICatalogRepository
  parse: APIParseRepository

  // Download
  downloadFormat: APIDownloadFormatRepository
  download: APIDownloadRepository

  // Label Type
  categoryType: APILabelRepository
  spanType: APILabelRepository
  relationType: APILabelRepository

  // Label
  category: APICategoryRepository
  span: APISpanRepository
  relation: APIRelationRepository
  textLabel: APITextLabelRepository
  boundingBox: APIBoundingBoxRepository
  segmentation: APISegmentationRepository
}

declare module 'vue/types/vue' {
  interface Vue {
    readonly $repositories: Repositories
  }
}

const repositories: Repositories = {
  // User
  auth: new APIAuthRepository(),
  user: new APIUserRepository(),

  // Project
  project: new APIProjectRepository(),
  member: new APIMemberRepository(),
  role: new APIRoleRepository(),
  tag: new APITagRepository(),
  perspective: new APIPerspectiveRepository(),
  question: new APIQuestionRepository(),
  optionsGroup: new APIOptionsGroupRepository(),
  optionsQuestion: new APIOptionsQuestionRepository(),
  questionType: new APIQuestionTypeRepository(),
  answer: new APIAnswerRepository(),
  votingConfiguration: new APIVotingConfigurationRepository(),
  annotationRuleType: new APIAnnotationRuleTypeRepository(),
  annotationRule: new APIAnnotationRuleRepository(),
  annotationRuleAnswer: new APIAnnotationRuleAnswerRepository(),

  // Example
  example: new APIExampleRepository(),
  comment: new APICommentRepository(),
  taskStatus: new APITaskStatusRepository(),
  metrics: new APIMetricsRepository(),
  statistics: new APIStatisticsRepository(),
  option: new LocalStorageOptionRepository(),
  assignment: new APIAssignmentRepository(),

  // Auto Labeling
  config: new APIConfigRepository(),
  template: new APITemplateRepository(),

  // Upload
  catalog: new APICatalogRepository(),
  parse: new APIParseRepository(),

  // Download
  downloadFormat: new APIDownloadFormatRepository(),
  download: new APIDownloadRepository(),

  // Label Type
  categoryType: new APILabelRepository('category-type'),
  spanType: new APILabelRepository('span-type'),
  relationType: new APILabelRepository('relation-type'),

  // Label
  category: new APICategoryRepository(),
  span: new APISpanRepository(),
  relation: new APIRelationRepository(),
  textLabel: new APITextLabelRepository(),
  boundingBox: new APIBoundingBoxRepository(),
  segmentation: new APISegmentationRepository()
}

const plugin: Plugin = (_, inject) => {
  inject('repositories', repositories)
}

export default plugin
export { repositories }
