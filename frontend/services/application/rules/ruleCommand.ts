import {
    AnnotationRuleDTO,
    AnnotationRuleTypeDTO,
    AnnotationRuleAnswerDTO,
    VotingConfigurationDTO,
  } from './ruleData';
  
  export type CreateAnnotationRuleTypeCommand = Omit<AnnotationRuleTypeDTO, 'id'>;
  
  export type CreateAnnotationRuleCommand = Omit<AnnotationRuleDTO, 'id'>;
  
  export type CreateVotingConfigurationCommand = Omit<VotingConfigurationDTO, 'id'>;
  
  export type CreateAnnotationRuleAnswerCommand = Omit<AnnotationRuleAnswerDTO, 'id'>;