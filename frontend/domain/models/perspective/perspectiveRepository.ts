import { PerspectiveItem } from './perspective'

export interface PerspectiveRepository {
  create(projectId: string, item: PerspectiveItem): Promise<PerspectiveItem>
  list(projectId: string): Promise<PerspectiveItem | null>
  listAll(): Promise<PerspectiveItem[]>
  get(projectId: string, perspectiveId: string): Promise<PerspectiveItem>
}
