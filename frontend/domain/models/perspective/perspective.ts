import { PerspectiveRepository } from './perspectiveRepository'
import { QuestionItem } from './question/question'

export class PerspectiveItem {
  constructor(
    readonly id: number,
    readonly project_id: number,
    readonly questions: QuestionItem[],
    readonly members: number[]
  ) {}

  static create(project_id: number, questions: QuestionItem[], members: number[]): PerspectiveItem {
    return new PerspectiveItem(0, project_id, questions, members)
  }

  static async list(repository: PerspectiveRepository, project_id: string): Promise<PerspectiveItem[]> {
    const items = await repository.list(project_id)
    return Array.isArray(items) ? items : [items]
  }
}
