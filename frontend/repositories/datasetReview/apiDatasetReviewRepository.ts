import ApiService from '@/services/api.service'
import { DatasetReviewItem } from '~/domain/models/datasetReview/datasetReview'

function toModel(item: { [key: string]: any }): DatasetReviewItem {
  return new DatasetReviewItem(
    item.id,
    item.example,
    item.user,
    item.is_approved,
    item.comment,
    item.label_agreements
  )
}

function toPayload(item: DatasetReviewItem): { [key: string]: any } {
  return {
    example: item.example,
    user: item.user,
    is_approved: item.is_approved,
    comment: item.comment,
    label_agreements: item.label_agreements
  }
}

export class ApiDatasetReviewRepository {
  constructor(private readonly request = ApiService) {}

  async list(projectId: string): Promise<DatasetReviewItem[]> {
    const url = `/projects/${projectId}/dataset-reviews/list`
    const response = await this.request.get(url)
    return response.data.map((item: { [key: string]: any }) => toModel(item))
  }

  async create(projectId: string, item: DatasetReviewItem): Promise<DatasetReviewItem> {
    const url = `/projects/${projectId}/dataset-reviews/`
    const payload = toPayload(item)
    const response = await this.request.post(url, payload)
    return toModel(response.data)
  }
}
