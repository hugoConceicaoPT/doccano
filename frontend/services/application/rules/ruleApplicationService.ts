import {
  CreateAnnotationRuleCommand,
  CreateAnnotationRuleAnswerCommand,
  CreateVotingConfigurationCommand
} from './ruleCommand'
import { AnnotationRuleDTO, AnnotationRuleAnswerDTO, VotingConfigurationDTO } from './ruleData'
import {
  AnnotationRuleRepository,
  AnnotationRuleAnswerRepository,
  VotingConfigurationRepository
} from '~/domain/models/rules/ruleRepository'
import {
  AnnotationRuleAnswerItem,
  AnnotationRuleItem,
  VotingConfigurationItem
} from '~/domain/models/rules/rule'

export class AnnotationRuleApplicationService {
  constructor(private readonly repository: AnnotationRuleRepository) {}

  public async create(
    projectId: string,
    item: CreateAnnotationRuleCommand
  ): Promise<AnnotationRuleDTO> {
    const annotationRule = new AnnotationRuleItem(
      0,
      item.project,
      item.name,
      item.voting_configuration,
      '',
      false
    )
    const created = await this.repository.create(projectId, annotationRule)
    return new AnnotationRuleDTO(created)
  }

  public async list(projectId: string): Promise<AnnotationRuleItem[]> {
    return await this.repository.list(projectId)
  }

  public async listUnvoted(projectId: string): Promise<{
    rules: AnnotationRuleItem[],
    activeVotings: any[],
    totalUnvotedRules: number
  }> {
    return await this.repository.listUnvoted(projectId)
  }

  public async findById(projectId: string, id: number): Promise<AnnotationRuleDTO> {
    const item = await this.repository.findById(projectId, id)
    if (!item) {
      throw new Error('AnnotationRuleItem not found')
    }
    return new AnnotationRuleDTO(item)
  }

  public async update(projectId: string, id: number, data: any): Promise<AnnotationRuleDTO> {
    const updated = await this.repository.update(
      projectId,
      id,
      data as Partial<import('~/domain/models/rules/rule').AnnotationRuleItem>
    )
    return new AnnotationRuleDTO(updated)
  }
}

export class VotingConfigurationApplicationService {
  constructor(private readonly repository: VotingConfigurationRepository) {}

  public async create(
    projectId: string,
    item: CreateVotingConfigurationCommand
  ): Promise<VotingConfigurationDTO> {
    const votingConfiguration = new VotingConfigurationItem(
      0,
      item.project,
      item.voting_threshold,
      item.percentage_threshold,
      item.created_by,
      item.begin_date,
      item.end_date
    )
    const created = await this.repository.create(projectId, votingConfiguration)
    return new VotingConfigurationDTO(created)
  }

  public async findById(projectId: string, id: number): Promise<VotingConfigurationDTO> {
    const item = await this.repository.findById(projectId, id)
    if (!item) {
      throw new Error('VotingConfigurationItem not found')
    }
    return new VotingConfigurationDTO(item)
  }

  public async list(projectId: string): Promise<VotingConfigurationItem[]> {
    return await this.repository.list(projectId)
  }

  public async update(
    projectId: string,
    id: number,
    data: Partial<VotingConfigurationItem>
  ): Promise<VotingConfigurationDTO> {
    const updated = await this.repository.update(projectId, id, data)
    return new VotingConfigurationDTO(updated)
  }
}

export class AnnotationRuleAnswerApplicationService {
  constructor(private readonly repository: AnnotationRuleAnswerRepository) {}

  public async create(
    projectId: string,
    item: CreateAnnotationRuleAnswerCommand
  ): Promise<AnnotationRuleAnswerDTO> {
    const annotationRuleAnswer = new AnnotationRuleAnswerItem(
      0,
      item.annotation_rule,
      item.member,
      item.answer
    )
    const created = await this.repository.create(projectId, annotationRuleAnswer)
    return new AnnotationRuleAnswerDTO(created)
  }

  public async list(
    projectId: string,
    annotationRuleId: number
  ): Promise<AnnotationRuleAnswerItem[]> {
    return await this.repository.list(projectId, annotationRuleId)
  }

  public async delete(projectId: string, id: number): Promise<void> {
    await this.repository.delete(projectId, id)
  }

  public async update(
    projectId: string,
    id: number,
    data: Partial<AnnotationRuleAnswerItem>
  ): Promise<AnnotationRuleAnswerDTO> {
    const updated = await this.repository.update(projectId, id, data)
    return new AnnotationRuleAnswerDTO(updated)
  }
}
