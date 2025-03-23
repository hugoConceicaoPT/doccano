export class AnswerItem {
  constructor(
    readonly id: number,
    readonly answer: string,
    readonly memberId: number,
    readonly questionId: number
  ) {}

  static create(answer: string, memberId: number, questionId: number): AnswerItem {
    return new AnswerItem(0, answer, memberId, questionId)
  }
}
