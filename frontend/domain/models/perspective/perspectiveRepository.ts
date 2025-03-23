import { PerspectiveItem } from './perspective'

export interface PerspectiveRepository {
  create(projectId: string, item: PerspectiveItem): Promise<PerspectiveItem>
}
