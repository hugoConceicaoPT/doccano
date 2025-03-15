import { UserItem } from './user'

export interface UserRepository {
  create(item: UserItem): Promise<UserItem>
  list(): Promise<UserItem[]>
}
