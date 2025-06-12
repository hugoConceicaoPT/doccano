import { OptionsQuestionItem, OptionsGroupItem, QuestionItem } from './question'

export interface QuestionRepository {
  create(projectId: string, item: QuestionItem): Promise<QuestionItem>
  list(perspectiveId: number, project_id: string): Promise<QuestionItem[]>
}

export interface OptionsGroupRepository {
  create(projectId: string, item: OptionsGroupItem): Promise<OptionsGroupItem>
  findByName(projectId: string, name: string): Promise<OptionsGroupItem>
  list(project_id: string) : Promise<OptionsGroupItem[]>
}

export interface OptionsQuestionRepository {
  create(projectId: string, item: OptionsQuestionItem): Promise<OptionsQuestionItem>
  list(projectId: string): Promise<OptionsQuestionItem[]>
}


