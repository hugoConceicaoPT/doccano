import { QuestionItem } from './question'

export interface QuestionRepository {
  create(item: QuestionItem): Promise<QuestionItem>
  list(): Promise<QuestionItem[]>
}
