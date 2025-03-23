import { CreateQuestionCommand } from './questionCommand'
import { QuestionDTO } from './questionData'
import { AnswerItem } from '~/domain/models/perspective/answer/answer'
import { QuestionItem } from '~/domain/models/perspective/question/question'
import { QuestionRepository } from '~/domain/models/perspective/question/questionRepository'

export class QuestionApplicationService {
  constructor(private readonly repository: QuestionRepository) {}

  public async create(item: CreateQuestionCommand): Promise<QuestionDTO> {
    const answers = item.answers.map((a) => new AnswerItem(0, a.answer, a.memberId, a.questionId))
    const question = new QuestionItem(0, item.question, answers)

    const created = await this.repository.create(question)
    return new QuestionDTO(created)
  }
}
