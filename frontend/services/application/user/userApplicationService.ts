import { UserDTO } from './userData'
import { CreateUserCommand } from './userCommand'
import { UserRepository } from '~/domain/models/user/userRepository'
import { UserItem } from '~/domain/models/user/user'

export class UserApplicationService {
  constructor(private readonly repository: UserRepository) {}

  public async create(item: CreateUserCommand): Promise<UserDTO> {
    const user = UserItem.create(
      item.username,
      item.password,
      item.passwordConfirmation,
      item.isSuperUser,
      item.isStaff
    )
    const created = await this.repository.create(user)
    return new UserDTO(created)
  }

  public bulkDelete(items: UserDTO[]): Promise<void> {
      const ids = items.map((item) => item.id)
      return this.repository.delete(ids)
    }
  public async list(): Promise<UserDTO[]> {
    const users = await this.repository.list()
    return users.map((user) => new UserDTO(user))
  }
}
