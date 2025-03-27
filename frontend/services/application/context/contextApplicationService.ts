import { Context } from '~/domain/models/context/context'
import { ContextTagRepository } from '~/domain/models/context/contextRepository'

export class ContextApplicationService {
  constructor(private readonly repository: ContextTagRepository) {}

  public createContext(exampleId: string | number, text: string): Promise<Context> {
    return this.repository.create(exampleId, text)
  }

  public listContext(exampleId: string | number): Promise<Context[]> {
    return this.repository.list(exampleId)
  }

  public deleteContext(exampleId: string | number, contextId: number): Promise<void> {
    return this.repository.delete(exampleId, contextId)
  }
}
