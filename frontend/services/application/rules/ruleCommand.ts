import {
    AnnotationRuleDTO,
    AnnotationRuleTypeDTO,
    AnnotationRuleAnswerDTO,
    VotingConfigurationDTO,
  } from './ruleData';
  
  export type CreateAnnotationRuleTypeCommand = Omit<AnnotationRuleTypeDTO, 'id'>;
  
  export interface CreateAnnotationRuleCommand {
    project: number;
    name: string;
    description: string;
    voting_configuration: number;
    annotation_rule_type: number;
  }
  
  export type CreateVotingConfigurationCommand = Omit<VotingConfigurationDTO, 'id'>;
  
  export type CreateAnnotationRuleAnswerCommand = Omit<AnnotationRuleAnswerDTO, 'id'>;