import { AnswerItem } from '../answer/answer'
import {
  QuestionRepository
} from './questionRepository'

export class QuestionItem {
  constructor(
    readonly id: number,
    readonly question: string,
    readonly answers: AnswerItem[],
    readonly perspective_id: number,
    readonly answer_type?: string
  ) {}

  static create(
    question: string,
    answers: AnswerItem[] = [],
    perspective_id: number,
    answer_type?: string
  ): QuestionItem {
    return new QuestionItem(0, question, answers, perspective_id, answer_type)
  }

  static list(
    repository: QuestionRepository,
    perspectiveId: number,
    project_id: string
  ): Promise<QuestionItem[]> {
    return repository.list(perspectiveId, project_id)
  }
}
