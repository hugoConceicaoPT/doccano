// frontend/src/domain/models/rule/rule.ts

import {
    AnnotationRuleTypeRepository,
    AnnotationRuleRepository,
    VotingConfigurationRepository,
    AnnotationRuleAnswerRepository,
  } from './ruleRepository';
  
  export class AnnotationRuleTypeItem {
    constructor(
      readonly id: number,
      readonly annotation_rule_type: string,
    ) {}
  
    static create(
      annotation_rule_type: string,
    ): AnnotationRuleTypeItem {
      return new AnnotationRuleTypeItem(
        0,
        annotation_rule_type,
      );
    }
  
    static async list(repository: AnnotationRuleTypeRepository, projectId: string): Promise<AnnotationRuleTypeItem[]> {
      return await repository.list(projectId);
    }
  
    async delete(repository: AnnotationRuleTypeRepository, projectId: string): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível excluir um tipo de regra sem ID válido.');
      }
      await repository.delete(projectId, this.id);
    }
  
    async update(repository: AnnotationRuleTypeRepository, projectId: string): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível atualizar um tipo de regra sem ID válido.');
      }
  
      const updatedFields: Record<string, any> = {
        annotation_rule_type: this.annotation_rule_type,
      };
  
      await repository.update(projectId, this.id, updatedFields);
    }
  }
  
  export class AnnotationRuleItem {
    constructor(
      readonly id: number,
      readonly project: number,
      readonly description: string,
      readonly voting_configuration: number,
      readonly annotation_rule_type: number,
    ) {}
  
    static create(
      project: number,
      description: string,
      voting_configuration: number,
      annotation_rule_type: number,
    ): AnnotationRuleItem {
      return new AnnotationRuleItem(
        0,
        project,
        description,
        voting_configuration,
        annotation_rule_type,
      );
    }
  
    static async list(repository: AnnotationRuleRepository, projectId: string): Promise<AnnotationRuleItem[]> {
      return await repository.list(projectId);
    }
  
    async delete(repository: AnnotationRuleRepository, projectId: string): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível excluir uma regra de anotação sem ID válido.');
      }
      await repository.delete(projectId, this.id);
    }
  
    async update(repository: AnnotationRuleRepository, projectId: string): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível atualizar uma regra de anotação sem ID válido.');
      }
  
      const updatedFields: Record<string, any> = {
        project: this.project,
        description: this.description,
        voting_configuration: this.voting_configuration,
        annotation_rule_type: this.annotation_rule_type,
      };
  
      await repository.update(projectId, this.id, updatedFields);
    }
  }
  
  export class VotingConfigurationItem {
    constructor(
      readonly id: number,
      readonly project: number,
      readonly annotation_rule_type: number,
      readonly voting_threshold: number,
      readonly created_by: number | null,
      readonly begin_date: string,
      readonly end_date: string,
    ) {}
  
    static create(
      project: number,
      annotation_rule_type: number,
      voting_threshold: number,
      created_by: number | null,
      begin_date: string,
      end_date: string,
    ): VotingConfigurationItem {
      return new VotingConfigurationItem(
        0,
        project,
        annotation_rule_type,
        voting_threshold,
        created_by,
        begin_date,
        end_date,
      );
    }
  
    static async findById(repository: VotingConfigurationRepository, projectId: string, id: number): Promise<VotingConfigurationItem | null> {
      return await repository.findById(projectId, id);
    }
  
    async update(repository: VotingConfigurationRepository, projectId: string): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível atualizar uma configuração de votação sem ID válido.');
      }
  
      const updatedFields: Record<string, any> = {
        project: this.project,
        annotation_rule_type: this.annotation_rule_type,
        voting_threshold: this.voting_threshold,
        begin_date: this.begin_date,
        end_date: this.end_date,
      };
  
      await repository.update(projectId, this.id, updatedFields);
    }
  }
  
  export class AnnotationRuleAnswerItem {
    constructor(
      readonly id: number,
      readonly annotation_rule: number,
      readonly member: number,
      readonly answer: boolean,
      readonly annotation_rule_type: number,
    ) {}
  
    static create(
      annotation_rule: number,
      member: number,
      answer: boolean,
      annotation_rule_type: number,
    ): AnnotationRuleAnswerItem {
      return new AnnotationRuleAnswerItem(
        0,
        annotation_rule,
        member,
        answer,
        annotation_rule_type,
      );
    }
  
    static async list(repository: AnnotationRuleAnswerRepository, projectId: string, annotationRuleId: number): Promise<AnnotationRuleAnswerItem[]> {
      return await repository.list(projectId, annotationRuleId);
    }
  
    async save(repository: AnnotationRuleAnswerRepository, projectId: string): Promise<void> {
      await repository.create(projectId, this); // Assuming create can handle existing IDs for update
    }
  }