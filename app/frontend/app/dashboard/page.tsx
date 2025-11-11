'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'

export default function DashboardPage() {
  const router = useRouter()
  const [engagements, setEngagements] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    try {
      const [userResponse, engagementsResponse] = await Promise.all([
        api.getCurrentUser(),
        api.listEngagements()
      ])
      setUser(userResponse)
      setEngagements(engagementsResponse.engagements)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleLogout = () => {
    localStorage.removeItem('access_token')
    router.push('/auth/login')
  }
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">Valuation Workbench</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <h2 className="text-3xl font-bold text-gray-900">Engagements</h2>
          <Link href="/dashboard/new" className="btn-primary">
            + New Engagement
          </Link>
        </div>
        
        {engagements.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600 mb-4">No engagements yet. Create your first engagement to get started.</p>
            <Link href="/dashboard/new" className="btn-primary">
              Create Engagement
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {engagements.map((engagement) => (
              <Link
                key={engagement.id}
                href={`/dashboard/engagements/${engagement.id}`}
                className="card hover:shadow-lg transition-shadow cursor-pointer"
              >
                <h3 className="text-lg font-semibold mb-2">{engagement.name}</h3>
                {engagement.client_name && (
                  <p className="text-sm text-gray-600 mb-2">Client: {engagement.client_name}</p>
                )}
                <div className="flex justify-between items-center text-xs text-gray-500 mt-4">
                  <span className="px-2 py-1 bg-gray-100 rounded">{engagement.status}</span>
                  <span>{new Date(engagement.created_at).toLocaleDateString()}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

