import {
    AnnotationRuleItem,
    AnnotationRuleTypeItem,
    VotingConfigurationItem,
    AnnotationRuleAnswerItem,
  } from '~/domain/models/rules/rule';
  
  export class AnnotationRuleTypeDTO {
    id: number;
    annotation_rule_type: string;
  
    constructor(item: AnnotationRuleTypeItem) {
      this.id = item.id;
      this.annotation_rule_type = item.annotation_rule_type;
    }
  }
  
  export class AnnotationRuleDTO {
    id: number;
    project: number;
    name: string;
    description: string;
    voting_configuration: number;
    annotation_rule_type: number;
  
    constructor(item: AnnotationRuleItem) {
      this.id = item.id;
      this.project = item.project;
      this.name = item.name;
      this.description = item.description;
      this.voting_configuration = item.voting_configuration;
      this.annotation_rule_type = item.annotation_rule_type;
    }
  }
  
  export class VotingConfigurationDTO {
    id: number;
    project: number;
    annotation_rule_type: number;
    example: number;
    voting_threshold: number;
    percentage_threshold: number;
    boolean_threshold: boolean;
    created_by: number | null;
    begin_date: string;
    end_date: string;
  
    constructor(item: VotingConfigurationItem) {
      this.id = item.id;
      this.project = item.project;
      this.annotation_rule_type = item.annotation_rule_type;
      this.example = item.example;
      this.voting_threshold = item.voting_threshold;
      this.percentage_threshold = item.percentage_threshold;
      this.boolean_threshold = item.boolean_threshold;
      this.created_by = item.created_by;
      this.begin_date = item.begin_date;
      this.end_date = item.end_date;
    }
  }
  
  export class AnnotationRuleAnswerDTO {
    id: number;
    annotation_rule: number;
    member: number;
    answer: boolean;
    annotation_rule_type: number;
  
    constructor(item: AnnotationRuleAnswerItem) {
      this.id = item.id;
      this.annotation_rule = item.annotation_rule;
      this.member = item.member;
      this.answer = item.answer;
      this.annotation_rule_type = item.annotation_rule_type;
    }
  }