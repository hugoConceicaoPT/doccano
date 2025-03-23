import { PerspectiveDTO } from './perspectiveData'

export type CreatePerspectiveCommand = Omit<PerspectiveDTO, 'id'>
