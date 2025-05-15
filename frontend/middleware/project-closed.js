export default function ({ redirect, params, app }) {
  const projectId = params.id
  if (projectId) {
    const isClosed = localStorage.getItem(`project_closed_${projectId}`) === 'true'
    if (isClosed) {
      return redirect(app.localePath(`/projects/${projectId}`))
    }
  }
} 