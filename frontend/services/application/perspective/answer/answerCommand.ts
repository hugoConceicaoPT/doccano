import { AnswerDTO } from './answerData'

export type CreateAnswerCommand = Omit<AnswerDTO, 'id'>
