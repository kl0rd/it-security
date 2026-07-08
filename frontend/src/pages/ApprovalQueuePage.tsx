import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { AccessRequest } from '../types';

export default function ApprovalQueuePage() {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const loadRequests = () => {
    api.get<AccessRequest[]>('/approvals')
      .then((r) => setRequests(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadRequests(); }, []);

  const approve = async (id: number) => {
    setActionLoading(id);
    try {
      await api.post(`/approvals/${id}`, { approved: true });
      loadRequests();
    } finally {
      setActionLoading(null);
    }
  };

  const reject = async (id: number) => {
    const reason = window.prompt('Rejection reason:');
    if (!reason) return;
    setActionLoading(id);
    try {
      await api.post(`/approvals/${id}`, { approved: false, rejection_reason: reason });
      loadRequests();
    } finally {
      setActionLoading(null);
    }
  };

  const thStyle: React.CSSProperties = {
    textAlign: 'left', padding: '0.6rem 0.75rem', fontSize: '0.75rem',
    fontWeight: 600, color: '#6b7280', textTransform: 'uppercase',
    background: '#f9fafb', borderBottom: '1px solid #e5e7eb',
  };
  const tdStyle: React.CSSProperties = {
    padding: '0.6rem 0.75rem', fontSize: '0.875rem', borderBottom: '1px solid #f3f4f6', verticalAlign: 'top',
  };

  if (loading) return <p>Loading…</p>;

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Approval Queue</h2>
      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['ID', 'Title', 'Type', 'Target DB', 'SQL Preview', 'Submitted', 'Actions'].map((h) => (
                <th key={h} style={thStyle}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {requests.map((req) => (
              <tr key={req.id}>
                <td style={tdStyle}>#{req.id}</td>
                <td style={tdStyle}>
                  <Link to={`/requests/${req.id}`} style={{ color: '#3b82f6', textDecoration: 'none' }}>
                    {req.title}
                  </Link>
                </td>
                <td style={tdStyle}>{req.request_type.replace(/_/g, ' ')}</td>
                <td style={tdStyle}>{req.target_pdb || req.target_db_service} @ {req.target_db_host}</td>
                <td style={{ ...tdStyle, maxWidth: 300 }}>
                  <code style={{ fontSize: '0.8rem', background: '#f3f4f6', padding: '2px 4px', borderRadius: 3 }}>
                    {req.execution_sql?.substring(0, 80)}…
                  </code>
                </td>
                <td style={tdStyle}>{new Date(req.created_at).toLocaleDateString()}</td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => approve(req.id)}
                      disabled={actionLoading === req.id}
                      style={{ background: '#10b981', color: '#fff', border: 'none', padding: '0.35rem 0.75rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.8rem' }}
                    >
                      ✓ Approve
                    </button>
                    <button
                      onClick={() => reject(req.id)}
                      disabled={actionLoading === req.id}
                      style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '0.35rem 0.75rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.8rem' }}
                    >
                      ✗ Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {requests.length === 0 && (
          <p style={{ padding: '2rem', color: '#6b7280', textAlign: 'center' }}>No requests pending approval.</p>
        )}
      </div>
    </div>
  );
}
