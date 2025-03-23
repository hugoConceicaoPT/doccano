import ApiService from '@/services/api.service'
import { PerspectiveItem } from '~/domain/models/perspective/perspective'
import { QuestionItem } from '~/domain/models/perspective/question/question'

function toModel(item: { [key: string]: any }): QuestionItem {
  return new QuestionItem(item.id, item.question, item.answers)
}

function toPayload(item: QuestionItem): { [key: string]: any } {
  return {
    id: item.id,
    question: item.question,
    answers: item.answers
  }
}

export class APIQuestionRepository {
  constructor(private readonly baseUrl = 'perspective', private readonly request = ApiService) {}

  async list(username?: string): Promise<PerspectiveItem[]> {
    let url = `/${this.baseUrl}s`

    if (username) {
      url += `?search=${encodeURIComponent(username)}`
    }

    const response = await this.request.get(url)
    return response.data.map((item: { [key: string]: any }) => toModel(item))
  }

  async create(projectId: string, item: QuestionItem): Promise<QuestionItem> {
    const url = `/projects/${projectId}/perspectives/${this.baseUrl}s/create`
    const payload = toPayload(item)
    const response = await this.request.post(url, payload)
    return toModel(response.data)
  }
}
