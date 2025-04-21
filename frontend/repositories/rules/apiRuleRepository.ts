import {
    AnnotationRuleTypeRepository,
    AnnotationRuleRepository,
    VotingConfigurationRepository,
    AnnotationRuleAnswerRepository,
  } from '@/domain/models/rules/ruleRepository';
  import {
    AnnotationRuleTypeItem,
    AnnotationRuleItem,
    VotingConfigurationItem,
    AnnotationRuleAnswerItem,
  } from '@/domain/models/rules/rule';
  import ApiService from '@/services/api.service';
  
  
  function toAnnotationRuleTypeModel(item: { [key: string]: any }): AnnotationRuleTypeItem {
    return new AnnotationRuleTypeItem(item.id, item.annotation_rule_type);
  }
  
  function toAnnotationRuleModel(item: { [key: string]: any }): AnnotationRuleItem {
    return new AnnotationRuleItem(
      item.id,
      item.project,
      item.description,
      item.voting_configuration,
      item.annotation_rule_type
    );
  }
  
  function toVotingConfigurationModel(item: { [key: string]: any }): VotingConfigurationItem {
    return new VotingConfigurationItem(
      item.id,
      item.project,
      item.annotation_rule_type,
      item.voting_threshold,
      item.created_by,
      item.begin_date,
      item.end_date
    );
  }
  
  function toAnnotationRuleAnswerModel(item: { [key: string]: any }): AnnotationRuleAnswerItem {
    return new AnnotationRuleAnswerItem(
      item.id,
      item.annotation_rule,
      item.member,
      item.answer,
      item.annotation_rule_type
    );
  }
  
  
  export class APIAnnotationRuleTypeRepository implements AnnotationRuleTypeRepository {
    constructor(private readonly baseUrl = 'projects', private readonly request = ApiService) {}
  
    async create(projectId: string, item: AnnotationRuleTypeItem): Promise<AnnotationRuleTypeItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-types/create`;
      const response = await this.request.post(url, { annotation_rule_type: item.annotation_rule_type });
      return toAnnotationRuleTypeModel(response.data);
    }
  
    async list(projectId: string): Promise<AnnotationRuleTypeItem[]> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-types`;
      const response = await this.request.get(url);
      return response.data.map((item: { [key: string]: any }) => toAnnotationRuleTypeModel(item));
    }
  
    async delete(projectId: string, id: number): Promise<AnnotationRuleTypeItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-types/${id}`;
      const response = await this.request.delete(url);
      return toAnnotationRuleTypeModel(response.data);
    }
  
    async update(projectId: string, id: number, data: Partial<AnnotationRuleTypeItem>): Promise<AnnotationRuleTypeItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-types/${id}`;
      const response = await this.request.put(url, data);
      return toAnnotationRuleTypeModel(response.data);
    }
  
    async findById(projectId: string, id: number): Promise<AnnotationRuleTypeItem | null> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-types/${id}`;
      const response = await this.request.get(url);
      return toAnnotationRuleTypeModel(response.data);
    }
  }
  
  export class APIAnnotationRuleRepository implements AnnotationRuleRepository {
    constructor(private readonly baseUrl = 'projects', private readonly request = ApiService) {}
  
    async create(projectId: string, item: AnnotationRuleItem): Promise<AnnotationRuleItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rules/create`;
      const response = await this.request.post(url, item);
      return toAnnotationRuleModel(response.data);
    }
  
    async list(projectId: string): Promise<AnnotationRuleItem[]> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rules/list`;
      const response = await this.request.get(url);
      return response.data.map((item: { [key: string]: any }) => toAnnotationRuleModel(item));
    }
  
    async delete(projectId: string, id: number): Promise<AnnotationRuleItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rules/${id}`;
      const response = await this.request.delete(url);
      return toAnnotationRuleModel(response.data);
    }
  
    async update(projectId: string, id: number, data: Partial<AnnotationRuleItem>): Promise<AnnotationRuleItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rules/${id}`;
      const response = await this.request.put(url, data);
      return toAnnotationRuleModel(response.data);
    }
  
    async findById(projectId: string, id: number): Promise<AnnotationRuleItem | null> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rules/${id}`;
      const response = await this.request.get(url);
      return toAnnotationRuleModel(response.data);
    }
  }
  
  export class APIVotingConfigurationRepository implements VotingConfigurationRepository {
    constructor(private readonly baseUrl = 'projects', private readonly request = ApiService) {}
  
    async create(projectId: string, item: VotingConfigurationItem): Promise<VotingConfigurationItem> {
      const url = `/${this.baseUrl}/${projectId}/rules/create`;
      const response = await this.request.post(url, item);
      return toVotingConfigurationModel(response.data);
    }
  
    async findById(projectId: string, id: number): Promise<VotingConfigurationItem | null> {
      const url = `/${this.baseUrl}/${projectId}/voting-configurations/${id}`;
      const response = await this.request.get(url);
      return toVotingConfigurationModel(response.data);
    }
  
    async list(projectId: string): Promise<VotingConfigurationItem[]> {
      const url = `/${this.baseUrl}/${projectId}/rules/list`;
      const response = await this.request.get(url);
      return response.data.map((item: { [key: string]: any }) => toVotingConfigurationModel(item));
    }
  
    async update(projectId: string, id: number, data: Partial<VotingConfigurationItem>): Promise<VotingConfigurationItem> {
      const url = `/${this.baseUrl}/${projectId}/voting-configurations/${id}`;
      const response = await this.request.put(url, data);
      return toVotingConfigurationModel(response.data);
    }
  }
  
  export class APIAnnotationRuleAnswerRepository implements AnnotationRuleAnswerRepository {
    constructor(private readonly baseUrl = 'projects', private readonly request = ApiService) {}
  
    async create(projectId: string, item: AnnotationRuleAnswerItem): Promise<AnnotationRuleAnswerItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-answers/create`;
      const response = await this.request.post(url, item);
      return toAnnotationRuleAnswerModel(response.data);
    }
  
    async list(projectId: string, annotationRuleId: number): Promise<AnnotationRuleAnswerItem[]> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-answers?annotation_rule=${annotationRuleId}`;
      const response = await this.request.get(url);
      return response.data.map((item: { [key: string]: any }) => toAnnotationRuleAnswerModel(item));
    }
  
    async delete(projectId: string, id: number): Promise<void> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-answers/${id}`;
      await this.request.delete(url);
    }
  
    async update(projectId: string, id: number, data: Partial<AnnotationRuleAnswerItem>): Promise<AnnotationRuleAnswerItem> {
      const url = `/${this.baseUrl}/${projectId}/annotation-rule-answers/${id}`;
      const response = await this.request.put(url, data);
      return toAnnotationRuleAnswerModel(response.data);
    }
  }