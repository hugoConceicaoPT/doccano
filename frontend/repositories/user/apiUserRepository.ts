import { UserItem } from '@/domain/models/user/user'
import ApiService from '@/services/api.service'

function toModel(item: { [key: string]: any }): UserItem {
  return new UserItem(item.id, item.username, item.is_superuser, item.is_staff)
}

export class APIUserRepository {
  constructor(private readonly baseUrl = 'user', private readonly request = ApiService) {}

  async getProfile(): Promise<UserItem> {
    const url = '/me'
    const response = await this.request.get(url)
    return toModel(response.data)
  }

  async list(projectId: string): Promise<UserItem[]> {
    const url = `/projects/${projectId}/${this.baseUrl}s`
    const response = await this.request.get(url)
    return response.data.map((item: { [key: string]: any }) => toModel(item))
  }
}
