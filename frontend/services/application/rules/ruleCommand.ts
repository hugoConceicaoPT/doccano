import { AnnotationRuleDTO, AnnotationRuleAnswerDTO, VotingConfigurationDTO } from './ruleData'

export type CreateAnnotationRuleCommand = Omit<AnnotationRuleDTO, 'id'>

export type CreateVotingConfigurationCommand = Omit<VotingConfigurationDTO, 'id'>

export type CreateAnnotationRuleAnswerCommand = Omit<AnnotationRuleAnswerDTO, 'id'>
