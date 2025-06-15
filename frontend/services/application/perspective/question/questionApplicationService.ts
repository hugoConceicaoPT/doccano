import {
  CreateQuestionCommand
} from './questionCommand'
import { QuestionDTO } from './questionData'
import { AnswerItem } from '~/domain/models/perspective/answer/answer'
import {
  QuestionItem
} from '~/domain/models/perspective/question/question'
import {
  QuestionRepository
} from '~/domain/models/perspective/question/questionRepository'

export class QuestionApplicationService {
  constructor(private readonly repository: QuestionRepository) {}

  public async create(projectId: string, item: CreateQuestionCommand): Promise<QuestionDTO> {
    const answers = item.answers.map(
      (a) => new AnswerItem(0, a.member, a.question, a.answer_text, a.answer_option)
    )
    const question = new QuestionItem(
      0,
      item.question,
      answers,
      item.perspective_id ?? 0,

      item.answer_type
    )

    const created = await this.repository.create(projectId, question)
    return new QuestionDTO(created)
  }

  public async list(perspectiveId: number, projectId: string): Promise<QuestionItem[]> {
    return await this.repository.list(perspectiveId, projectId)
  }
}
