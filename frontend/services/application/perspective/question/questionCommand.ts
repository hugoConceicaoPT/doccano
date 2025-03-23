import { CreateAnswerCommand } from '../answer/answerCommand'
import { QuestionDTO } from './questionData'

export type CreateQuestionCommand = Omit<QuestionDTO, 'id'> & {
  answers: CreateAnswerCommand[]
}
