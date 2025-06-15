import { DatasetReviewDTO } from "./datasetReviewData"

export type CreateDatasetReviewCommand = Omit<DatasetReviewDTO, 'id'>


