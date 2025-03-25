import { UserRepository } from './userRepository'

export class UserItem {
  constructor(
    readonly id: number,
    readonly username: string,
    readonly password: string,
    readonly passwordConfirmation: string,
    readonly isSuperUser: boolean,
    readonly isStaff: boolean,
    readonly firstName?: string,
    readonly lastName?: string,
    readonly email?: string
  ) {}

  static create(
    username: string,
    password: string,
    passwordConfirmation: string,
    isSuperUser: boolean,
    isStaff: boolean,
    firstName?: string,
    lastName?: string,
    email?: string
  ): UserItem {
    return new UserItem(0, username, password, passwordConfirmation, isSuperUser, isStaff, firstName, lastName, email)
  }

  static async list(repository: UserRepository): Promise<UserItem[]> {
    return await repository.list()
  }

  async delete(repository: UserRepository): Promise<void> {
    if (this.id === 0) {
      throw new Error('Não é possível excluir um usuário sem ID válido.')
    }
    await repository.delete(this.id)
  }

  async update(repository: UserRepository): Promise<void> {
    if (this.id === 0) {
      throw new Error("Não é possível atualizar um usuário sem ID válido.")
    }

    if (this.password !== this.passwordConfirmation) {
      throw new Error("A confirmação de senha não confere.")
    }

    await repository.update(this.id, {
      username: this.username,
      password: this.password
    })
  }
}
