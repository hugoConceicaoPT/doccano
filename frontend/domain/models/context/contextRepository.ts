import { Context } from '~/domain/models/context/context'

export interface ContextTagRepository {
  list(exampleId: string | number): Promise<Context[]>

  create(exampleId: string | number, item: string): Promise<Context>

  delete(exampleId: string | number, tagId: number): Promise<void>
}
