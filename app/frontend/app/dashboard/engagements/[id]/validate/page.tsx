'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

interface Mapping {
  source_id: string;
  source_name: string;
  target_id: string;
  target_name: string;
  confidence: number;
  reasoning: string;
  status: string;
}

export default function ValidatePage() {
  const params = useParams();
  const router = useRouter();
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    loadMappings();
  }, []);

  const loadMappings = async () => {
    try {
      const response = await fetch(`/api/v1/${params.id}/mappings`);
      const data = await response.json();
      setMappings(data.mappings || []);
      setSummary(data.summary);
    } catch (error) {
      console.error('Error loading mappings:', error);
    } finally {
      setLoading(false);
    }
  };

  const approveMapping = async (mappingId: string) => {
    try {
      await fetch(`/api/v1/${params.id}/mappings/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mapping_ids: [mappingId],
          action: 'approve'
        })
      });
      
      setMappings(mappings.map(m =>
        m.source_id === mappingId ? { ...m, status: 'approved' } : m
      ));
    } catch (error) {
      console.error('Error approving mapping:', error);
    }
  };

  const rejectMapping = async (mappingId: string) => {
    try {
      await fetch(`/api/v1/${params.id}/mappings/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mapping_ids: [mappingId],
          action: 'reject'
        })
      });
      
      setMappings(mappings.map(m =>
        m.source_id === mappingId ? { ...m, status: 'rejected' } : m
      ));
    } catch (error) {
      console.error('Error rejecting mapping:', error);
    }
  };

  const approveAll = async () => {
    const pendingIds = mappings
      .filter(m => m.status === 'pending')
      .map(m => m.source_id);
    
    if (pendingIds.length === 0) return;
    
    try {
      await fetch(`/api/v1/${params.id}/mappings/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mapping_ids: pendingIds,
          action: 'approve'
        })
      });
      
      setMappings(mappings.map(m =>
        pendingIds.includes(m.source_id) ? { ...m, status: 'approved' } : m
      ));
    } catch (error) {
      console.error('Error approving all:', error);
    }
  };

  const proceedToValuation = () => {
    router.push(`/dashboard/engagements/${params.id}/valuation`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Review AI Mappings</h1>
        <p className="text-gray-600">
          Review and approve AI-suggested mappings to canonical chart of accounts
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border">
            <p className="text-sm text-gray-600">Total Items</p>
            <p className="text-2xl font-bold">{summary.total_items}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <p className="text-sm text-green-700">High Confidence</p>
            <p className="text-2xl font-bold text-green-700">{summary.high_confidence}</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-700">Medium Confidence</p>
            <p className="text-2xl font-bold text-yellow-700">{summary.medium_confidence}</p>
          </div>
          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
            <p className="text-sm text-red-700">Low Confidence</p>
            <p className="text-2xl font-bold text-red-700">{summary.low_confidence}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={approveAll}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Approve All High Confidence
        </button>
        <button
          onClick={proceedToValuation}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Proceed to Valuation →
        </button>
      </div>

      {/* Mappings Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Source Line Item
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Mapped To
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Status
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {mappings.map((mapping) => (
              <tr key={mapping.source_id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <p className="font-medium">{mapping.source_name}</p>
                  <p className="text-xs text-gray-500">{mapping.reasoning}</p>
                </td>
                <td className="px-4 py-3">
                  <p className="font-medium">{mapping.target_name}</p>
                  <p className="text-xs text-gray-500">{mapping.target_id}</p>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          mapping.confidence > 0.9
                            ? 'bg-green-500'
                            : mapping.confidence > 0.7
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${mapping.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {(mapping.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      mapping.status === 'approved'
                        ? 'bg-green-100 text-green-800'
                        : mapping.status === 'rejected'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {mapping.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {mapping.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => approveMapping(mapping.source_id)}
                        className="text-green-600 hover:text-green-800 text-sm"
                      >
                        ✓ Approve
                      </button>
                      <button
                        onClick={() => rejectMapping(mapping.source_id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        ✗ Reject
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
