import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { AccessRequest } from '../types';
import { useAuth } from '../context/AuthContext';

function statusColor(status: string): string {
  const map: Record<string, string> = {
    draft: '#6b7280', pending_approval: '#f59e0b', approved: '#3b82f6',
    rejected: '#ef4444', executed: '#10b981', failed: '#dc2626', rolled_back: '#8b5cf6',
  };
  return map[status] || '#6b7280';
}

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [req, setReq] = useState<AccessRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  const loadRequest = () => {
    api.get<AccessRequest>(`/requests/${id}`)
      .then((r) => setReq(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadRequest(); }, [id]);

  const doAction = async (action: () => Promise<void>) => {
    setActionLoading(true);
    setError('');
    try {
      await action();
      loadRequest();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  const codeStyle: React.CSSProperties = {
    background: '#1e293b', color: '#e2e8f0', padding: '1rem',
    borderRadius: 6, fontFamily: 'monospace', fontSize: '0.875rem',
    overflow: 'auto', whiteSpace: 'pre-wrap', margin: '0.5rem 0',
  };

  if (loading) return <p>Loading…</p>;
  if (!req) return <p>Request not found.</p>;

  const canApprove = (user?.role === 'admin' || user?.role === 'approver') && req.requester_id !== user?.id;
  const canExecute = user?.role === 'admin';

  return (
    <div>
      <button
        onClick={() => navigate(-1)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6b7280', marginBottom: '1rem' }}
      >
        ← Back
      </button>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
        <div>
          <h2>{req.title}</h2>
          <p style={{ color: '#6b7280', marginTop: '0.25rem' }}>{req.description}</p>
        </div>
        <span style={{
          background: statusColor(req.status), color: '#fff',
          padding: '4px 14px', borderRadius: 20, fontSize: '0.875rem', fontWeight: 600,
        }}>
          {req.status.replace(/_/g, ' ').toUpperCase()}
        </span>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626', padding: '0.75rem', borderRadius: 4, marginBottom: '1rem', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {/* Details grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        {[
          ['Request Type', req.request_type.replace(/_/g, ' ')],
          ['Target Database', `${req.target_pdb || req.target_db_service} @ ${req.target_db_host}:${req.target_db_port}`],
          ['Created', new Date(req.created_at).toLocaleString()],
          ['Approved At', req.approved_at ? new Date(req.approved_at).toLocaleString() : '—'],
          ['Executed At', req.executed_at ? new Date(req.executed_at).toLocaleString() : '—'],
          ['Rejection Reason', req.rejection_reason || '—'],
        ].map(([label, value]) => (
          <div key={label} style={{ background: '#fff', borderRadius: 8, padding: '1rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
            <div style={{ fontSize: '0.875rem' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* SQL */}
      <div style={{ background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '0.75rem' }}>Generated SQL</h3>
        <div>
          <strong style={{ fontSize: '0.8rem', color: '#6b7280' }}>Execution SQL</strong>
          <pre style={codeStyle}>{req.execution_sql || '—'}</pre>
        </div>
        <div style={{ marginTop: '0.75rem' }}>
          <strong style={{ fontSize: '0.8rem', color: '#6b7280' }}>Rollback SQL</strong>
          <pre style={codeStyle}>{req.rollback_sql || '—'}</pre>
        </div>
      </div>

      {/* Execution output */}
      {(req.execution_output || req.execution_error) && (
        <div style={{ background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '0.75rem' }}>Execution Result</h3>
          {req.execution_output && <pre style={{ ...codeStyle, background: '#052e16', color: '#86efac' }}>{req.execution_output}</pre>}
          {req.execution_error && <pre style={{ ...codeStyle, background: '#450a0a', color: '#fca5a5' }}>{req.execution_error}</pre>}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {req.status === 'draft' && req.requester_id === user?.id && (
          <button
            onClick={() => doAction(() => api.post(`/requests/${req.id}/submit`).then(() => {}))}
            disabled={actionLoading}
            style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
          >
            Submit for Approval
          </button>
        )}
        {req.status === 'pending_approval' && canApprove && (
          <>
            <button
              onClick={() => doAction(() => api.post(`/approvals/${req.id}`, { approved: true }).then(() => {}))}
              disabled={actionLoading}
              style={{ background: '#10b981', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
            >
              Approve
            </button>
            <button
              onClick={() => {
                const reason = window.prompt('Rejection reason:');
                if (reason) doAction(() => api.post(`/approvals/${req.id}`, { approved: false, rejection_reason: reason }).then(() => {}));
              }}
              disabled={actionLoading}
              style={{ background: '#ef4444', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
            >
              Reject
            </button>
          </>
        )}
        {req.status === 'approved' && canExecute && (
          <button
            onClick={() => {
              if (window.confirm('Execute this request against the database?'))
                doAction(() => api.post(`/execution/${req.id}/execute`).then(() => {}));
            }}
            disabled={actionLoading}
            style={{ background: '#1a2533', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
          >
            Execute
          </button>
        )}
        {(req.status === 'executed' || req.status === 'failed') && canExecute && (
          <button
            onClick={() => {
              if (window.confirm('Run rollback SQL against the database?'))
                doAction(() => api.post(`/execution/${req.id}/rollback`).then(() => {}));
            }}
            disabled={actionLoading}
            style={{ background: '#8b5cf6', color: '#fff', border: 'none', padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
          >
            Rollback
          </button>
        )}
      </div>
    </div>
  );
}
