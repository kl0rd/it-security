import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { AccessRequest, AuditLog } from '../types';
import { useAuth } from '../context/AuthContext';

const cardStyle: React.CSSProperties = {
  background: '#fff', borderRadius: 8, padding: '1.5rem',
  boxShadow: '0 1px 4px rgba(0,0,0,0.08)', flex: 1, minWidth: 160,
};

const statNumStyle: React.CSSProperties = {
  fontSize: '2rem', fontWeight: 700, color: '#1a2533',
};

function statusColor(status: string): string {
  const map: Record<string, string> = {
    draft: '#6b7280',
    pending_approval: '#f59e0b',
    approved: '#3b82f6',
    rejected: '#ef4444',
    executed: '#10b981',
    failed: '#ef4444',
    rolled_back: '#8b5cf6',
  };
  return map[status] || '#6b7280';
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [pending, setPending] = useState<AccessRequest[]>([]);
  const [recentAudit, setRecentAudit] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<AccessRequest[]>('/requests'),
      (user?.role === 'admin' || user?.role === 'approver')
        ? api.get<AccessRequest[]>('/approvals')
        : Promise.resolve({ data: [] as AccessRequest[] }),
      api.get<AuditLog[]>('/audit?limit=5'),
    ])
      .then(([reqRes, appRes, auditRes]) => {
        setRequests(reqRes.data);
        setPending(appRes.data);
        setRecentAudit(auditRes.data);
      })
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <p>Loading…</p>;

  const byStatus = requests.reduce((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Dashboard</h2>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <div style={cardStyle}>
          <div style={statNumStyle}>{requests.length}</div>
          <div style={{ color: '#6b7280', fontSize: '0.875rem' }}>My Requests</div>
        </div>
        {Object.entries(byStatus).map(([status, count]) => (
          <div key={status} style={cardStyle}>
            <div style={{ ...statNumStyle, color: statusColor(status) }}>{count}</div>
            <div style={{ color: '#6b7280', fontSize: '0.875rem' }}>{status.replace(/_/g, ' ')}</div>
          </div>
        ))}
        {(user?.role === 'admin' || user?.role === 'approver') && (
          <div style={cardStyle}>
            <div style={{ ...statNumStyle, color: '#f59e0b' }}>{pending.length}</div>
            <div style={{ color: '#6b7280', fontSize: '0.875rem' }}>Pending Approval</div>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Recent requests */}
        <div style={{ background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem' }}>Recent Requests</h3>
            <Link to="/requests/new" style={{ background: '#1a2533', color: '#fff', padding: '0.4rem 0.8rem', borderRadius: 4, textDecoration: 'none', fontSize: '0.8rem' }}>
              + New Request
            </Link>
          </div>
          {requests.slice(0, 5).map((req) => (
            <Link key={req.id} to={`/requests/${req.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '0.6rem 0', borderBottom: '1px solid #f3f4f6',
              }}>
                <span style={{ fontSize: '0.875rem' }}>{req.title}</span>
                <span style={{
                  background: statusColor(req.status), color: '#fff',
                  padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem',
                }}>
                  {req.status.replace(/_/g, ' ')}
                </span>
              </div>
            </Link>
          ))}
          {requests.length === 0 && <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>No requests yet.</p>}
        </div>

        {/* Recent audit */}
        <div style={{ background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem' }}>Recent Audit Events</h3>
            <Link to="/audit" style={{ color: '#3b82f6', fontSize: '0.8rem', textDecoration: 'none' }}>View all</Link>
          </div>
          {recentAudit.map((log) => (
            <div key={log.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <div style={{ fontSize: '0.875rem' }}>
                <strong>{log.actor_username}</strong> — {log.action}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                {new Date(log.created_at).toLocaleString()}
              </div>
            </div>
          ))}
          {recentAudit.length === 0 && <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>No audit events.</p>}
        </div>
      </div>
    </div>
  );
}
