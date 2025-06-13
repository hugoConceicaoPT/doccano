import ApiService from '@/services/api.service'
import { PerspectiveItem } from '~/domain/models/perspective/perspective'
import { QuestionItem } from '~/domain/models/perspective/question/question'

function toModel(item: { [key: string]: any }): PerspectiveItem {
  // Mapear as perguntas do formato do backend para o formato do frontend
  const questions = item.questions ? item.questions.map((q: any) => new QuestionItem(
    q.id,
    q.question,
    q.answers || [],
    item.id, // perspective_id
    q.answer_type
  )) : []

  return new PerspectiveItem(
    item.id, 
    item.name, 
    item.project_id, 
    questions, 
    item.members || []
  )
}

function toPayload(item: PerspectiveItem): { [key: string]: any } {
  return {
    id: item.id,
    name: item.name,
    project_id: item.project_id,
    questions: item.questions,
    members: item.members
  }
}

export class APIPerspectiveRepository {
  constructor(private readonly baseUrl = 'perspective', private readonly request = ApiService) {}

  async list(projectId: string): Promise<PerspectiveItem | null> {
    const url = `/projects/${projectId}/${this.baseUrl}s`
    const response = await this.request.get(url)
    if (response.data.length === 0) {
      return null // Retorna null quando não há perspectivas em vez de lançar erro
    }
    return toModel(response.data[0]) // Retorna apenas o primeiro item
  }

  async create(projectId: string, item: PerspectiveItem): Promise<PerspectiveItem> {
    const url = `/projects/${projectId}/${this.baseUrl}s/create`
    const payload = toPayload(item)
    const response = await this.request.post(url, payload)
    return toModel(response.data)
  }

  async listAll(): Promise<PerspectiveItem[]> {
    const url = `/${this.baseUrl}s/all`
    const response = await this.request.get(url)
    return response.data.map((item: any) => toModel(item))
  }

  async get(projectId: string, perspectiveId: string): Promise<PerspectiveItem> {
    const url = `/projects/${projectId}/${this.baseUrl}s/${perspectiveId}`
    const response = await this.request.get(url)
    return toModel(response.data)
  }
}
