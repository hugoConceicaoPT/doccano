import ApiService from '@/services/api.service'
import { Distribution } from '~/domain/models/statistics/statistics'

export class APIStatisticsRepository {
  constructor(private readonly request = ApiService) {}

  async fetchPerspectiveAnswerDistribution(projectId: string): Promise<Distribution> {
    const url = `/projects/${projectId}/statistics/perspective-answer-distribution`
    const response = await this.request.get(url)
    return response.data
  }
}
