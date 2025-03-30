export class AnswerItem {
  constructor(
    readonly id: number,
    readonly member: number,
    readonly question: number,
    readonly answer_text?: string,
    readonly answer_option?: string
  ) {}

  static create(member: number, question: number, answer_text?: string, answer_option?: string): AnswerItem {
    return new AnswerItem(0, member, question, answer_text, answer_option);
  }

  static list(items: { member: number, question: number, answer_text?: string, answer_option?: string }[]): AnswerItem[] {
    return items.map(item => AnswerItem.create(item.member, item.question, item.answer_text, item.answer_option));
  }
}
