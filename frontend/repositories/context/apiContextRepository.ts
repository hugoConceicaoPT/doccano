

import { Context } from '@/domain/models/context/context'
import { ContextTagRepository } from '@/domain/models/context/contextRepository'
import ApiService from '@/services/api.service'

function toModel(item: { [key: string]: any }): Context {
  return new Context(item.id, item.text, item.example)
}

export class APIContextRepository implements ContextTagRepository {
  constructor(private readonly request = ApiService) {}

  async list(exampleId: string | number): Promise<Context[]> {
    const url = `/v1/annotations/${exampleId}/context`
    const response = await this.request.get(url)
    return response.data.map((item: { [key: string]: any }) => toModel(item))
  }

  async create(exampleId: string | number, text: string): Promise<Context> {
    const url = `/v1/annotations/${exampleId}/context`
    const response = await this.request.post(url, { text })
    return toModel(response.data)
  }

  async delete(exampleId: string | number, contextId: number): Promise<void> {
    const url = `/v1/annotations/${exampleId}/context/${contextId}`
    await this.request.delete(url)
  }
}