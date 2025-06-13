import {
  AnnotationRuleTypeItem,
  AnnotationRuleItem,
  VotingConfigurationItem,
  AnnotationRuleAnswerItem
} from './rule'

export interface AnnotationRuleTypeRepository {
  create(projectId: string, item: AnnotationRuleTypeItem): Promise<AnnotationRuleTypeItem>
  list(projectId: string): Promise<AnnotationRuleTypeItem[]>
  delete(projectId: string, id: number): Promise<AnnotationRuleTypeItem>
  update(
    projectId: string,
    id: number,
    data: Partial<AnnotationRuleTypeItem>
  ): Promise<AnnotationRuleTypeItem>
  findById(projectId: string, id: number): Promise<AnnotationRuleTypeItem | null>
}

export interface AnnotationRuleRepository {
  create(projectId: string, item: AnnotationRuleItem): Promise<AnnotationRuleItem>
  list(projectId: string): Promise<AnnotationRuleItem[]>
  delete(projectId: string, id: number): Promise<AnnotationRuleItem>
  update(
    projectId: string,
    id: number,
    data: Partial<AnnotationRuleItem>
  ): Promise<AnnotationRuleItem>
  findById(projectId: string, id: number): Promise<AnnotationRuleItem | null>
}

export interface VotingConfigurationRepository {
  create(projectId: string, item: VotingConfigurationItem): Promise<VotingConfigurationItem>
  findById(projectId: string, id: number): Promise<VotingConfigurationItem | null>
  list(projectId: string): Promise<VotingConfigurationItem[]>
  update(
    projectId: string,
    id: number,
    data: Partial<VotingConfigurationItem>
  ): Promise<VotingConfigurationItem>
}

export interface AnnotationRuleAnswerRepository {
  create(projectId: string, item: AnnotationRuleAnswerItem): Promise<AnnotationRuleAnswerItem>
  list(projectId: string, annotationRuleId: number): Promise<AnnotationRuleAnswerItem[]>
  delete(projectId: string, id: number): Promise<void>
  update(
    projectId: string,
    id: number,
    data: Partial<AnnotationRuleAnswerItem>
  ): Promise<AnnotationRuleAnswerItem>
}
