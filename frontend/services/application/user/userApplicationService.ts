import { UserDTO } from './userData'
import { CreateUserCommand } from './userCommand'
import { UserRepository } from '~/domain/models/user/userRepository'
import { UserItem } from '~/domain/models/user/user'

export class UserApplicationService {
  constructor(private readonly repository: UserRepository) {}

  public async create(projectId: string, item: CreateUserCommand): Promise<UserDTO> {
    const user = UserItem.create(
      item.username,
      item.password,
      item.passwordConfirmation,
      item.isSuperUser,
      item.isStaff
    )
    const created = await this.repository.create(projectId, user)
    return new UserDTO(created)
  }
}
