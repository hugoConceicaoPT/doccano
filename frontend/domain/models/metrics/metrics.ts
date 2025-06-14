export type Label = { [key: string]: number }
export type User = { [key: string]: number }
export type ConfirmedCount = { [key: string]: number }
export type Distribution = {
  [userId: string]: {
    [exampleId: string]: {
      [label: string]: number
    }
  }
}
export type DiscussionPerRule = { [rule: string]: number }
export type Percentage = { [example: string]: { [label: string]: number } }
export interface Progress {
  total: number
  progress: { user: string; done: number }[]
}

export interface MyProgress {
  total: number
  complete: number
  remaining: number
}
