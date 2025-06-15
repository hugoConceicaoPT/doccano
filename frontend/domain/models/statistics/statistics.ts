export type Distribution = {
  [questionId: string]: {
    question: string
    answers: {
      [answerText: string]: {
        percentage: number
        annotator: string
      }
    }
    total: number
  }
}
