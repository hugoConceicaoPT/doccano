import { AnswerItem } from '../answer/answer'

export class QuestionItem {
  constructor(readonly id: number, readonly question: string, readonly answers: AnswerItem[]) {}

  static create(question: string, answers: AnswerItem[] = []): QuestionItem {
    return new QuestionItem(0, question, answers)
  }
}
