
import { CreateDatasetReviewCommand } from './datasetReviewCommand'
import { DatasetReviewDTO } from './datasetReviewData'
import { DatasetReviewItem } from '~/domain/models/datasetReview/datasetReview'
import { DatasetReviewRepository } from '~/domain/models/datasetReview/datasetReviewRepository'

export class DatasetReviewApplicationService {
    constructor(private readonly repository: DatasetReviewRepository) { }

    public async create(projectId: string, item: CreateDatasetReviewCommand): Promise<DatasetReviewDTO> {
        const datasetReview = DatasetReviewItem.create(
            item.example,
            item.is_approved,
            item.comment,
            item.label_agreements
        )
        const created = await this.repository.create(projectId, datasetReview)
        return new DatasetReviewDTO(created)
    }

    public async list(projectId: string): Promise<DatasetReviewDTO[]> {
        const datasetReview = await this.repository.list(projectId)
        if (!datasetReview) {
            return []
        }
        return datasetReview.map((datasetReview) => new DatasetReviewDTO(datasetReview))
    }
}