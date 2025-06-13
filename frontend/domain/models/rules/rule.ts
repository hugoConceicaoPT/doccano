import {
    AnnotationRuleRepository,
    VotingConfigurationRepository,
    AnnotationRuleAnswerRepository,
  } from './ruleRepository';
  
  export class AnnotationRuleItem {
    constructor(
      readonly id: number,
      readonly project: number,
      readonly name: string,
      readonly description: string,
      readonly voting_configuration: number,
      readonly final_result: string,
      readonly is_finalized: boolean
    ) {}
  
    static create(
      project: number,
      name: string,
      description: string,
      voting_configuration: number,
    ): AnnotationRuleItem {
      return new AnnotationRuleItem(
        0,
        project,
        name,
        description,
        voting_configuration,
        '',
        false
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
        name: this.name,
        description: this.description,
        voting_configuration: this.voting_configuration,
      };
  
      await repository.update(projectId, this.id, updatedFields);
    }
  }
  
  export class VotingConfigurationItem {
    constructor(
      readonly id: number,
      readonly project: number,
      readonly voting_threshold: number,
      readonly percentage_threshold: number,
      readonly created_by: number | null,
      readonly begin_date: string,
      readonly end_date: string,
      readonly is_closed: boolean = false,
      readonly version: number = 1
    ) {}
  
    static create(
      project: number,
      voting_threshold: number,
      percentage_threshold: number,
      created_by: number | null,
      begin_date: string,
      end_date: string,
      is_closed: boolean = false,
      version: number = 1
    ): VotingConfigurationItem {
      return new VotingConfigurationItem(
        0,
        project,
        voting_threshold,
        percentage_threshold,
        created_by,
        begin_date,
        end_date,
        is_closed,
        version
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
        voting_threshold: this.voting_threshold,
        percentage_threshold: this.percentage_threshold,
        begin_date: this.begin_date,
        end_date: this.end_date,
        is_closed: this.is_closed,
        version: this.version
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
    ) {}
  
    static create(
      annotation_rule: number,
      member: number,
      answer: boolean,
    ): AnnotationRuleAnswerItem {
      return new AnnotationRuleAnswerItem(
        0,
        annotation_rule,
        member,
        answer,
      );
    }
  
    static async list(repository: AnnotationRuleAnswerRepository, projectId: string, annotationRuleId: number): Promise<AnnotationRuleAnswerItem[]> {
      return await repository.list(projectId, annotationRuleId);
    }
  
    async save(repository: AnnotationRuleAnswerRepository, projectId: string): Promise<void> {
      await repository.create(projectId, this); // Assuming create can handle existing IDs for update
    }
  
    async delete(repository: AnnotationRuleAnswerRepository, projectId: string): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível excluir uma resposta de regra sem ID válido.');
      }
      await repository.delete(projectId, this.id);
    }
  
    async update(repository: AnnotationRuleAnswerRepository, projectId: string, data: Partial<AnnotationRuleAnswerItem>): Promise<void> {
      if (this.id === 0) {
        throw new Error('Não é possível atualizar uma resposta de regra sem ID válido.');
      }
      await repository.update(projectId, this.id, data);
    }
  }