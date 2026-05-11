import apiClient from './client'

export interface OrchestrationRequest {
  query: string
}

export interface OrchestrationResponse {
  success: boolean
  task_id: string
  message: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

export interface OrchestrationError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}

export async function triggerOrchestration(query: string): Promise<OrchestrationResponse> {
  if (!query || query.trim().length === 0) {
    throw new Error('Query is required')
  }

  const request: OrchestrationRequest = {
    query: query.trim()
  }

  try {
    const response = await apiClient.post<OrchestrationResponse>(
      '/api/orchestration/trigger',
      request
    )

    console.log('[Orchestration] Triggered successfully:', response.data)
    return response.data
  } catch (error) {
    if (error instanceof Error) {
      console.error('[Orchestration] Error:', error.message)
    }
    throw error
  }
}

export async function getOrchestrationStatus(taskId: string) {
  if (!taskId) {
    throw new Error('Task ID is required')
  }

  try {
    const response = await apiClient.get(`/api/orchestration/status/${taskId}`)
    return response.data
  } catch (error) {
    if (error instanceof Error) {
      console.error('[Orchestration Status] Error:', error.message)
    }
    throw error
  }
}