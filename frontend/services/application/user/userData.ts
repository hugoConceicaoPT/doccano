import { UserItem } from '~/domain/models/user/user'

export class UserDTO {
  id: number
  username: string
  password: string
  passwordConfirmation: string
  isSuperUser: boolean
  isStaff: boolean
  firstName?: string
  lastName?: string
  email?: string

  constructor(item: UserItem) {
    this.id = item.id
    this.username = item.username
    this.password = item.password
    this.passwordConfirmation = item.passwordConfirmation
    this.isSuperUser = item.isSuperUser
    this.isStaff = item.isStaff
    this.firstName = item.firstName ?? ''
    this.lastName = item.lastName ?? ''
    this.email = item.email ?? ''
  }
}
