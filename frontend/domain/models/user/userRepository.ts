import { UserItem } from './user'

export interface UserRepository {
  create(item: UserItem): Promise<UserItem>
  delete(userId: number[]): Promise<void>
}
