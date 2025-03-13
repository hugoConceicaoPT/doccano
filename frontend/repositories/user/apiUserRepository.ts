import { UserItem } from '@/domain/models/user/user'
import ApiService from '@/services/api.service'

function toModel(item: { [key: string]: any }): UserItem {
  return new UserItem(
    item.id,
    item.username,
    item.password,
    item.password_confirmation,
    item.is_superuser,
    item.is_staff
  )
}

function toPayload(item: UserItem): { [key: string]: any } {
  return {
    id: item.id,
    username: item.username,
    password1: item.password,
    password2: item.passwordConfirmation,
    is_superuser: item.isSuperUser,
    is_staff: item.isStaff
  }
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

  async create(item: UserItem): Promise<UserItem> {
    const url = `/${this.baseUrl}s/create`
    const payload = toPayload(item)
    const response = await this.request.post(url, payload)
    return toModel(response.data)
  }
}
