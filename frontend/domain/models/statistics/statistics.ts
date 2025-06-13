export type Distribution = {
  [questionId: string]: {
    question: string
    answers: {
      [answerText: string]: number
    }
    total: number
  }
}
