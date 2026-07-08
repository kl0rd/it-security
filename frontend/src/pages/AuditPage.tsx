import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { AuditLog } from '../types';

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actor, setActor] = useState('');
  const [action, setAction] = useState('');
  const [selected, setSelected] = useState<AuditLog | null>(null);

  const loadLogs = () => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '100' });
    if (actor) params.append('actor_username', actor);
    if (action) params.append('action', action);
    api.get<AuditLog[]>(`/audit?${params}`)
      .then((r) => setLogs(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadLogs(); }, []);

  const thStyle: React.CSSProperties = {
    textAlign: 'left', padding: '0.6rem 0.75rem', fontSize: '0.75rem',
    fontWeight: 600, color: '#6b7280', textTransform: 'uppercase',
    background: '#f9fafb', borderBottom: '1px solid #e5e7eb',
  };
  const tdStyle: React.CSSProperties = {
    padding: '0.6rem 0.75rem', fontSize: '0.875rem', borderBottom: '1px solid #f3f4f6',
  };

  return (
    <div style={{ display: 'flex', gap: '1.5rem' }}>
      <div style={{ flex: 1 }}>
        <h2 style={{ marginBottom: '1.5rem' }}>Audit Log</h2>

        {/* Filters */}
        <div style={{ background: '#fff', borderRadius: 8, padding: '1rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 4 }}>Actor Username</label>
            <input value={actor} onChange={(e) => setActor(e.target.value)} style={{ padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: 4, fontSize: '0.875rem' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 4 }}>Action</label>
            <input value={action} onChange={(e) => setAction(e.target.value)} style={{ padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: 4, fontSize: '0.875rem' }} />
          </div>
          <button
            onClick={loadLogs}
            style={{ background: '#1a2533', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
          >
            Filter
          </button>
        </div>

        <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Time', 'Actor', 'Action', 'Request ID', 'Database', 'Result'].map((h) => (
                  <th key={h} style={thStyle}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr
                  key={log.id}
                  onClick={() => setSelected(log)}
                  style={{ cursor: 'pointer', background: selected?.id === log.id ? '#f0f9ff' : 'transparent' }}
                >
                  <td style={tdStyle}>{new Date(log.created_at).toLocaleString()}</td>
                  <td style={tdStyle}>{log.actor_username}</td>
                  <td style={tdStyle}>
                    <code style={{ background: '#f3f4f6', padding: '2px 6px', borderRadius: 3, fontSize: '0.8rem' }}>
                      {log.action}
                    </code>
                  </td>
                  <td style={tdStyle}>{log.access_request_id ? `#${log.access_request_id}` : '—'}</td>
                  <td style={tdStyle}>{log.target_db_host || '—'}</td>
                  <td style={tdStyle}>
                    <span style={{
                      color: log.success === 'success' ? '#10b981' : log.success === 'failure' ? '#ef4444' : '#6b7280',
                      fontWeight: 600, fontSize: '0.8rem',
                    }}>
                      {log.success}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <p style={{ padding: '1rem', color: '#6b7280' }}>Loading…</p>}
          {!loading && logs.length === 0 && <p style={{ padding: '2rem', color: '#6b7280', textAlign: 'center' }}>No audit logs found.</p>}
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div style={{ width: 380, background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', alignSelf: 'flex-start', position: 'sticky', top: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem' }}>Audit Detail</h3>
            <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: '#6b7280' }}>×</button>
          </div>
          {[
            ['ID', selected.id],
            ['Time', new Date(selected.created_at).toLocaleString()],
            ['Actor', selected.actor_username],
            ['Action', selected.action],
            ['Request', selected.access_request_id ? `#${selected.access_request_id}` : '—'],
            ['Database', selected.target_db_host || '—'],
            ['Service', selected.target_db_service || '—'],
            ['PDB', selected.target_pdb || '—'],
            ['Result', selected.result || '—'],
            ['Success', selected.success],
          ].map(([label, value]) => (
            <div key={String(label)} style={{ marginBottom: '0.5rem', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 600, display: 'block' }}>{label}</span>
              <span style={{ fontSize: '0.875rem' }}>{String(value)}</span>
            </div>
          ))}
          {selected.sql_executed && (
            <div>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 600 }}>SQL Executed</span>
              <pre style={{ background: '#1e293b', color: '#e2e8f0', padding: '0.75rem', borderRadius: 6, fontSize: '0.75rem', overflow: 'auto', marginTop: 4 }}>
                {selected.sql_executed}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
