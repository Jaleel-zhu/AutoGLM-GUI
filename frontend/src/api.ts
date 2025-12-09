import axios from 'redaxios'

export interface ChatResponse {
  result: string
  steps: number
  success: boolean
}

export interface StatusResponse {
  version: string
  initialized: boolean
  step_count: number
}

export interface InitRequest {
  base_url?: string
  model_name?: string
  device_id?: string | null
  max_steps?: number
}

export async function initAgent(config?: InitRequest): Promise<{ success: boolean; message: string }> {
  const res = await axios.post('/api/init', config ?? {})
  return res.data
}

export async function sendMessage(message: string): Promise<ChatResponse> {
  const res = await axios.post('/api/chat', { message })
  return res.data
}

export async function getStatus(): Promise<StatusResponse> {
  const res = await axios.get('/api/status')
  return res.data
}

export async function resetChat(): Promise<{ success: boolean; message: string }> {
  const res = await axios.post('/api/reset')
  return res.data
}
