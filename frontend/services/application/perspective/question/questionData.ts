import { AnswerDTO } from '../answer/answerData'
import { QuestionItem } from '~/domain/models/perspective/question/question'

export class QuestionDTO {
  id: number
  question: string
  answers: AnswerDTO[]
  perspective_id?: number
  answer_type?: string

  constructor(item: QuestionItem) {
    this.id = item.id
    this.question = item.question
    this.answers = item.answers.map((answer) => new AnswerDTO(answer))
    this.perspective_id = item.perspective_id
    this.answer_type = item.answer_type
  }
}
