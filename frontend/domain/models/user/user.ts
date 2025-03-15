export class UserItem {
  constructor(
    readonly id: number,
    readonly username: string,
    readonly password: string,
    readonly passwordConfirmation: string,
    readonly isSuperuser: boolean,
    readonly isStaff: boolean
  ) {}

  static create(
    username: string,
    password: string,
    passwordConfirmation: string,
    isSuperuser: boolean,
    isStaff: boolean
  ): UserItem {
    return new UserItem(0, username, password, passwordConfirmation, isSuperuser, isStaff)
  }
}
