export interface PerspectiveCheckResult {
  canProceed: boolean
  hasAnswers: boolean
  memberRole?: any
}

export interface PerspectiveCheckerEvents {
  cancelled: () => void
  'redirected-to-perspective': () => void
}

export interface PerspectiveCheckerProps {
  projectId: string | number
  isProjectAdmin: boolean
} 