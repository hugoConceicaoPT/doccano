import { DatasetReviewRepository } from "./datasetReviewRepository"

export class DatasetReviewItem {
    constructor(
      readonly id: number,
      readonly example: number,
      readonly user: number,
      readonly is_approved: boolean,
      readonly comment: string | null,
      readonly label_agreements: any[]
    ) {}
  
    static create(
      example: number,
      is_approved: boolean,
      comment: string | null = null,
      label_agreements: any[] = []
    ): DatasetReviewItem {
      return new DatasetReviewItem (
        0,
        example,
        0, // user will be set by backend
        is_approved,
        comment,
        label_agreements
      )
    }

    static async list(DatasetReviewRepository: DatasetReviewRepository, project_id: string): Promise<DatasetReviewItem[]> {
      return await DatasetReviewRepository.list(project_id)
    }
  }
  