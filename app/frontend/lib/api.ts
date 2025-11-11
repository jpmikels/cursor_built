/**
 * API client for VWB backend
 */
import axios, { AxiosInstance, AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

class APIClient {
  private client: AxiosInstance
  
  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    // Add request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    
    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('access_token')
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }
  
  // Auth
  async register(data: { email: string; password: string; full_name: string; tenant_name: string }) {
    const response = await this.client.post('/auth/register', data)
    return response.data
  }
  
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password })
    return response.data
  }
  
  async getCurrentUser() {
    const response = await this.client.get('/auth/me')
    return response.data
  }
  
  // Engagements
  async listEngagements(page: number = 1, pageSize: number = 20) {
    const response = await this.client.get('/engagements', {
      params: { page, page_size: pageSize }
    })
    return response.data
  }
  
  async createEngagement(data: any) {
    const response = await this.client.post('/engagements', data)
    return response.data
  }
  
  async getEngagement(id: number) {
    const response = await this.client.get(`/engagements/${id}`)
    return response.data
  }
  
  async updateEngagement(id: number, data: any) {
    const response = await this.client.patch(`/engagements/${id}`, data)
    return response.data
  }
  
  async deleteEngagement(id: number) {
    await this.client.delete(`/engagements/${id}`)
  }
  
  async getEngagementStatus(id: number) {
    const response = await this.client.get(`/engagements/${id}/status`)
    return response.data
  }
  
  // Documents
  async getUploadUrl(engagementId: number, filename: string, mimeType: string, documentType: string) {
    const response = await this.client.post(`/engagements/${engagementId}/upload`, {
      filename,
      mime_type: mimeType,
      document_type: documentType
    })
    return response.data
  }
  
  async uploadDocument(uploadUrl: string, file: File) {
    await axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type
      }
    })
  }
  
  async listDocuments(engagementId: number) {
    const response = await this.client.get(`/engagements/${engagementId}/documents`)
    return response.data
  }
  
  async startIngestion(engagementId: number, documentIds?: number[]) {
    const response = await this.client.post(`/engagements/${engagementId}/ingest`, {
      document_ids: documentIds
    })
    return response.data
  }
  
  // Validation
  async listValidationIssues(engagementId: number) {
    const response = await this.client.get(`/engagements/${engagementId}/validation`)
    return response.data
  }
  
  async acceptSuggestion(engagementId: number, issueId: number, notes?: string) {
    const response = await this.client.post(`/engagements/${engagementId}/validation/accept`, {
      issue_id: issueId,
      notes
    })
    return response.data
  }
  
  async overrideSuggestion(engagementId: number, issueId: number, action: string, notes: string) {
    const response = await this.client.post(`/engagements/${engagementId}/validation/override`, {
      issue_id: issueId,
      action,
      notes
    })
    return response.data
  }
  
  // Valuation
  async runValuation(engagementId: number, data: any) {
    const response = await this.client.post(`/engagements/${engagementId}/valuation/run`, data)
    return response.data
  }
  
  async getValuationResult(engagementId: number, runId?: number) {
    const params = runId ? { run_id: runId } : {}
    const response = await this.client.get(`/engagements/${engagementId}/valuation/result`, { params })
    return response.data
  }
  
  async listValuationRuns(engagementId: number) {
    const response = await this.client.get(`/engagements/${engagementId}/valuation/runs`)
    return response.data
  }
  
  // Artifacts
  async getWorkbookDownloadUrl(engagementId: number) {
    const response = await this.client.get(`/engagements/${engagementId}/artifacts/workbook.xlsx`)
    return response.data
  }
  
  async getSummaryDownloadUrl(engagementId: number) {
    const response = await this.client.get(`/engagements/${engagementId}/artifacts/summary.pdf`)
    return response.data
  }
}

export const api = new APIClient()

