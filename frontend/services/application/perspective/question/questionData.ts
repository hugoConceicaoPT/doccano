import { AnswerDTO } from '../answer/answerData'
import { QuestionItem } from '~/domain/models/perspective/question/question'

export class QuestionDTO {
  id: number
  question: string
  answers: AnswerDTO[]

  constructor(item: QuestionItem) {
    this.id = item.id
    this.question = item.question
    this.answers = item.answers.map((answer) => new AnswerDTO(answer))
  }
}
