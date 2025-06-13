import { AnnotationRepository } from '@/domain/models/tasks/annotationRepository'
import { Category } from '@/domain/models/tasks/category'

export class APICategoryRepository extends AnnotationRepository<Category> {
  labelName = 'categories'

  toModel(item: { [key: string]: any }): Category {
    return new Category(item.id, item.label, item.user)
  }

  toPayload(item: Category): { [key: string]: any } {
    return {
      id: item.id,
      label: item.label,
      user: item.user
    }
  }

  public async list(projectId: string, exampleId: number, allUsers: boolean = false): Promise<Category[]> {
    const url = this.baseUrl(projectId, exampleId)
    const params = allUsers ? { include_all: 'true' } : {}
    const response = await this.request.get(url, { params })
    return response.data.map((item: { [key: string]: any }) => this.toModel(item))
  }
}
