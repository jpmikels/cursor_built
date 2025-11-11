'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { api } from '@/lib/api'
import Link from 'next/link'

export default function EngagementDetailPage() {
  const params = useParams()
  const router = useRouter()
  const engagementId = parseInt(params.id as string)
  
  const [engagement, setEngagement] = useState<any>(null)
  const [status, setStatus] = useState<any>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  
  useEffect(() => {
    loadData()
  }, [engagementId])
  
  const loadData = async () => {
    try {
      const [engagementData, statusData, documentsData] = await Promise.all([
        api.getEngagement(engagementId),
        api.getEngagementStatus(engagementId),
        api.listDocuments(engagementId)
      ])
      setEngagement(engagementData)
      setStatus(statusData)
      setDocuments(documentsData)
    } catch (error) {
      console.error('Failed to load engagement:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleStartIngestion = async () => {
    try {
      await api.startIngestion(engagementId)
      alert('Ingestion started successfully')
      loadData()
    } catch (error) {
      alert('Failed to start ingestion')
    }
  }
  
  if (loading) {
    return <div className="p-8">Loading...</div>
  }
  
  if (!engagement) {
    return <div className="p-8">Engagement not found</div>
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/dashboard" className="text-primary-600 hover:text-primary-700">
                ← Back
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">{engagement.name}</h1>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['overview', 'upload', 'validation', 'valuation'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Engagement Details</h3>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Client</dt>
                  <dd className="text-sm text-gray-900">{engagement.client_name || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Currency</dt>
                  <dd className="text-sm text-gray-900">{engagement.currency}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Fiscal Year End</dt>
                  <dd className="text-sm text-gray-900">{engagement.fiscal_year_end || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="text-sm text-gray-900">{engagement.status}</dd>
                </div>
              </dl>
            </div>
            
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Status</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{status.documents_count}</div>
                  <div className="text-sm text-gray-600">Documents</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{status.parsed_documents}</div>
                  <div className="text-sm text-gray-600">Parsed</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{status.unresolved_issues}</div>
                  <div className="text-sm text-gray-600">Issues</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{status.valuations_count}</div>
                  <div className="text-sm text-gray-600">Valuations</div>
                </div>
              </div>
            </div>
            
            {status.current_jobs && status.current_jobs.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">Active Jobs</h3>
                <div className="space-y-2">
                  {status.current_jobs.map((job: any) => (
                    <div key={job.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{job.job_type}</span>
                      <span className="text-sm text-gray-600">{job.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'upload' && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Documents</h3>
            <div className="mb-4">
              <Link href={`/dashboard/engagements/${engagementId}/upload`} className="btn-primary">
                + Upload Documents
              </Link>
            </div>
            
            {documents.length === 0 ? (
              <p className="text-gray-600">No documents uploaded yet.</p>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <p className="text-sm font-medium">{doc.original_filename}</p>
                      <p className="text-xs text-gray-600">{doc.document_type}</p>
                    </div>
                    <div className="text-xs text-gray-500">
                      {doc.is_parsed ? (
                        <span className="text-green-600">✓ Parsed</span>
                      ) : (
                        <span className="text-gray-400">Not parsed</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {documents.length > 0 && !status.current_jobs?.some((j: any) => j.job_type === 'ingestion') && (
              <div className="mt-4">
                <button onClick={handleStartIngestion} className="btn-primary">
                  Start Processing
                </button>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'validation' && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Validation Issues</h3>
            <p className="text-gray-600">Validation results will appear here after processing.</p>
          </div>
        )}
        
        {activeTab === 'valuation' && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Valuation</h3>
            <Link href={`/dashboard/engagements/${engagementId}/valuation`} className="btn-primary">
              Run Valuation
            </Link>
            
            {status.latest_valuation && (
              <div className="mt-6">
                <h4 className="font-medium mb-2">Latest Valuation</h4>
                <div className="bg-gray-50 p-4 rounded">
                  <p className="text-sm">
                    <span className="font-medium">Run #{status.latest_valuation.run_number}</span>
                    {status.latest_valuation.concluded_value && (
                      <span className="ml-4 text-lg font-bold text-primary-600">
                                ${status.latest_valuation.concluded_value.toLocaleString()}
                    </span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(status.latest_valuation.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

