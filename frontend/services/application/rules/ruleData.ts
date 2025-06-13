import {
  AnnotationRuleItem,
  VotingConfigurationItem,
  AnnotationRuleAnswerItem
} from '~/domain/models/rules/rule'

export class AnnotationRuleDTO {
  id: number
  project: number
  name: string
  voting_configuration: number
  final_result: string
  is_finalized: boolean

  constructor(item: AnnotationRuleItem) {
    this.id = item.id
    this.project = item.project
    this.name = item.name
    this.voting_configuration = item.voting_configuration
  }
}

export class VotingConfigurationDTO {
  id: number
  project: number
  voting_threshold: number
  percentage_threshold: number
  created_by: number | null
  begin_date: string
  end_date: string
  is_closed: boolean
  version: number

  constructor(item: VotingConfigurationItem) {
    this.id = item.id
    this.project = item.project
    this.voting_threshold = item.voting_threshold
    this.percentage_threshold = item.percentage_threshold
    this.created_by = item.created_by
    this.begin_date = item.begin_date
    this.end_date = item.end_date
    this.is_closed = item.is_closed
    this.version = item.version
  }
}

export class AnnotationRuleAnswerDTO {
  id: number
  annotation_rule: number
  member: number
  answer: boolean

  constructor(item: AnnotationRuleAnswerItem) {
    this.id = item.id
    this.annotation_rule = item.annotation_rule
    this.member = item.member
    this.answer = item.answer
  }
}
