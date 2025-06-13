import {
  CreateOptionsGroupCommand,
  CreateOptionsQuestionCommand,
  CreateQuestionCommand
} from './questionCommand'
import { OptionsGroupDTO, OptionsQuestionDTO, QuestionDTO } from './questionData'
import { AnswerItem } from '~/domain/models/perspective/answer/answer'
import {
  OptionsGroupItem,
  OptionsQuestionItem,
  QuestionItem
} from '~/domain/models/perspective/question/question'
import {
  OptionsGroupRepository,
  OptionsQuestionRepository,
  QuestionRepository
} from '~/domain/models/perspective/question/questionRepository'

export class QuestionApplicationService {
  constructor(private readonly repository: QuestionRepository) {}

  public async create(projectId: string, item: CreateQuestionCommand): Promise<QuestionDTO> {
    const answers = item.answers.map(
      (a) => new AnswerItem(0, a.member, a.question, a.answer_text, a.answer_option)
    )
    const question = new QuestionItem(
      0,
      item.question,
      answers,
      item.perspective_id ?? 0,

      item.answer_type
    )

    const created = await this.repository.create(projectId, question)
    return new QuestionDTO(created)
  }

  public async list(perspectiveId: number, projectId: string): Promise<QuestionItem[]> {
    return await this.repository.list(perspectiveId, projectId)
  }
}
export class OptionsGroupApplicationService {
  constructor(private readonly repository: OptionsGroupRepository) {}

  public async create(
    project_id: string,
    item: CreateOptionsGroupCommand
  ): Promise<OptionsGroupDTO> {
    const optionsGroup = new OptionsGroupItem(0, item.name, item.options_questions)

    const created = await this.repository.create(project_id, optionsGroup)
    return new OptionsGroupDTO(created)
  }

  public async findByName(projectId: string, name: string): Promise<OptionsGroupDTO> {
    const item = await this.repository.findByName(projectId, name)
    return new OptionsGroupDTO(item)
  }

  public async list(project_id: string): Promise<OptionsGroupItem[]> {
    return await this.repository.list(project_id)
  }
}

export class OptionsQuestionApplicationService {
  constructor(private readonly repository: OptionsQuestionRepository) {}

  public async create(
    project_id: string,
    item: CreateOptionsQuestionCommand
  ): Promise<OptionsQuestionDTO> {
    const optionsQuestion = new OptionsQuestionItem(0, item.option, 0)

    const created = await this.repository.create(project_id, optionsQuestion)
    return new OptionsQuestionDTO(created)
  }

  public async list(project_id: string): Promise<OptionsQuestionItem[]> {
    return await this.repository.list(project_id)
  }
}
