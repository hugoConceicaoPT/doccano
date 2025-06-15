import { DatasetReviewItem } from './datasetReview'

export interface DatasetReviewRepository {
  create(projectId: string, item: DatasetReviewItem): Promise<DatasetReviewItem>
  list(projectId: string): Promise<DatasetReviewItem[]>
}