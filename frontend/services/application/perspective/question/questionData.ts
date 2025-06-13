import { AnswerDTO } from '../answer/answerData'
import { CreateOptionsQuestionCommand } from './questionCommand'
import { OptionsGroupItem, QuestionItem } from '~/domain/models/perspective/question/question'

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

export class OptionsQuestionDTO {
  id: number
  option: string

  constructor(item: OptionsQuestionDTO) {
    this.id = item.id
    this.option = item.option
  }
}

export class OptionsGroupDTO {
  id: number
  name: string
  options_questions: CreateOptionsQuestionCommand[]

  constructor(item: OptionsGroupItem) {
    this.id = item.id
    this.name = item.name
    this.options_questions = item.options_questions
  }
}
