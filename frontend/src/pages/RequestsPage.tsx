import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { AccessRequest } from '../types';

function statusColor(status: string): string {
  const map: Record<string, string> = {
    draft: '#6b7280', pending_approval: '#f59e0b', approved: '#3b82f6',
    rejected: '#ef4444', executed: '#10b981', failed: '#ef4444', rolled_back: '#8b5cf6',
  };
  return map[status] || '#6b7280';
}

export default function RequestsPage() {
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AccessRequest[]>('/requests')
      .then((r) => setRequests(r.data))
      .finally(() => setLoading(false));
  }, []);

  const thStyle: React.CSSProperties = {
    textAlign: 'left', padding: '0.6rem 0.75rem', fontSize: '0.75rem',
    fontWeight: 600, color: '#6b7280', textTransform: 'uppercase',
    background: '#f9fafb', borderBottom: '1px solid #e5e7eb',
  };
  const tdStyle: React.CSSProperties = {
    padding: '0.6rem 0.75rem', fontSize: '0.875rem', borderBottom: '1px solid #f3f4f6',
  };

  if (loading) return <p>Loading…</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>My Requests</h2>
        <Link
          to="/requests/new"
          style={{ background: '#1a2533', color: '#fff', padding: '0.5rem 1rem', borderRadius: 4, textDecoration: 'none', fontSize: '0.875rem', fontWeight: 600 }}
        >
          + New Request
        </Link>
      </div>

      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['ID', 'Title', 'Type', 'Status', 'Target DB', 'Created'].map((h) => (
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
                <td style={tdStyle}>
                  <span style={{
                    background: statusColor(req.status), color: '#fff',
                    padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem',
                  }}>
                    {req.status.replace(/_/g, ' ')}
                  </span>
                </td>
                <td style={tdStyle}>{req.target_pdb || req.target_db_service} @ {req.target_db_host}</td>
                <td style={tdStyle}>{new Date(req.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {requests.length === 0 && (
          <p style={{ padding: '2rem', color: '#6b7280', textAlign: 'center' }}>
            No requests found. <Link to="/requests/new">Create your first request</Link>.
          </p>
        )}
      </div>
    </div>
  );
}
