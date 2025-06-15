import { DatasetReviewItem } from "~/domain/models/datasetReview/datasetReview"


export class DatasetReviewDTO {
    id: number
    example: number
    user: number
    is_approved: boolean
    comment: string
    label_agreements: any[]

  constructor(item: DatasetReviewItem) {
    this.id = item.id
    this.example = item.example
    this.user = item.user
    this.is_approved = item.is_approved
    this.comment = item.comment ?? ''
    this.label_agreements = item.label_agreements
  }
}