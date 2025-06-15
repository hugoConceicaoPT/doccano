import { QuestionItem } from './question'

export interface QuestionRepository {
  create(projectId: string, item: QuestionItem): Promise<QuestionItem>
  list(perspectiveId: number, project_id: string): Promise<QuestionItem[]>
}