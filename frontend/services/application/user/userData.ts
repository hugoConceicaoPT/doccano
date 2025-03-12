import { UserItem } from '~/domain/models/user/user'

export class UserDTO {
  id: number
  username: string
  password: string
  passwordConfirmation: string
  isSuperUser: boolean
  isStaff: boolean

  constructor(item: UserItem) {
    this.id = item.id
    this.username = item.username
    this.password = item.password
    this.passwordConfirmation = item.passwordConfirmation
    this.isSuperUser = item.isSuperuser
    this.isStaff = item.isStaff
  }
}
