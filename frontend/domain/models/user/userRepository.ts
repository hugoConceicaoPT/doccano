import { UserItem } from './user'

export interface UserRepository {
  create(projectId: string, item: UserItem): Promise<UserItem>
}
