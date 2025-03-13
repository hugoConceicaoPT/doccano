export class UserItem {
  constructor(
    readonly id: number,
    readonly username: string,
    readonly password: string,
    readonly passwordConfirmation: string,
    readonly isSuperUser: boolean,
    readonly isStaff: boolean
  ) {}

  static create(
    username: string,
    password: string,
    passwordConfirmation: string,
    isSuperUser: boolean,
    isStaff: boolean
  ): UserItem {
    return new UserItem(0, username, password, passwordConfirmation, isSuperUser, isStaff)
  }
}
