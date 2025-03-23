import { AnswerDTO } from './answerData'
import { CreateAnswerCommand } from './answerCommand'
import { AnswerItem } from '~/domain/models/perspective/answer/answer'
import { AnswerRepository } from '~/domain/models/perspective/answer/answerRepository'

export class AnswerApplicationService {
  constructor(private readonly repository: AnswerRepository) {}

  public async create(item: CreateAnswerCommand): Promise<AnswerDTO> {
    const answer = AnswerItem.create(item.answer, item.memberId, item.questionId)
    const created = await this.repository.create(answer)
    return new AnswerDTO(created)
  }
}
