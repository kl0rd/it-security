import React, { useState } from 'react';
import api from '../services/api';
import { OracleUser, OracleRole, OracleInventorySummary } from '../types';

export default function InventoryPage() {
  const [host, setHost] = useState('');
  const [port, setPort] = useState('1521');
  const [service, setService] = useState('');
  const [pdb, setPdb] = useState('');
  const [summary, setSummary] = useState<OracleInventorySummary | null>(null);
  const [users, setUsers] = useState<OracleUser[]>([]);
  const [roles, setRoles] = useState<OracleRole[]>([]);
  const [activeTab, setActiveTab] = useState<'users' | 'roles'>('users');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadInventory = async () => {
    if (!host || !service) {
      setError('Host and Service Name are required');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const params = { host, port, service_name: service, ...(pdb ? { pdb } : {}) };
      const [sumRes, usrRes, roleRes] = await Promise.all([
        api.get<OracleInventorySummary>('/inventory/summary', { params }),
        api.get<OracleUser[]>('/inventory/users', { params }),
        api.get<OracleRole[]>('/inventory/roles', { params }),
      ]);
      setSummary(sumRes.data);
      setUsers(usrRes.data);
      setRoles(roleRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const thStyle: React.CSSProperties = {
    textAlign: 'left', padding: '0.6rem 0.75rem', fontSize: '0.75rem',
    fontWeight: 600, color: '#6b7280', textTransform: 'uppercase',
    background: '#f9fafb', borderBottom: '1px solid #e5e7eb',
  };
  const tdStyle: React.CSSProperties = {
    padding: '0.6rem 0.75rem', fontSize: '0.875rem', borderBottom: '1px solid #f3f4f6',
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>Oracle Inventory</h2>

      {/* Connection form */}
      <div style={{ background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          {[
            { label: 'Host', value: host, setter: setHost, placeholder: 'oracle.example.com' },
            { label: 'Port', value: port, setter: setPort, placeholder: '1521' },
            { label: 'Service Name', value: service, setter: setService, placeholder: 'ORCLPDB1' },
            { label: 'PDB (optional)', value: pdb, setter: setPdb, placeholder: 'MYPDB' },
          ].map(({ label, value, setter, placeholder }) => (
            <div key={label}>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 4 }}>{label}</label>
              <input
                value={value}
                onChange={(e) => setter(e.target.value)}
                placeholder={placeholder}
                style={{ padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: 4, fontSize: '0.875rem', width: 180 }}
              />
            </div>
          ))}
          <button
            onClick={loadInventory}
            disabled={loading}
            style={{
              background: '#1a2533', color: '#fff', border: 'none',
              padding: '0.55rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600,
            }}
          >
            {loading ? 'Loading…' : 'Load Inventory'}
          </button>
        </div>
        {error && <p style={{ color: '#dc2626', marginTop: '0.75rem', fontSize: '0.875rem' }}>{error}</p>}
      </div>

      {/* Summary */}
      {summary && (
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          {[
            { label: 'Users', value: summary.user_count },
            { label: 'Roles', value: summary.role_count },
            { label: 'System Privs', value: summary.sys_priv_count },
            { label: 'Object Privs', value: summary.obj_priv_count },
            { label: 'Profiles', value: summary.profile_count },
            { label: 'CDB', value: summary.is_cdb ? 'Yes' : 'No' },
          ].map(({ label, value }) => (
            <div key={label} style={{ background: '#fff', borderRadius: 8, padding: '1rem 1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', minWidth: 100 }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1a2533' }}>{value}</div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      {summary && (
        <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
          <div style={{ borderBottom: '1px solid #e5e7eb', display: 'flex' }}>
            {(['users', 'roles'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '0.75rem 1.5rem', border: 'none', background: 'none',
                  cursor: 'pointer', fontSize: '0.875rem', fontWeight: 500,
                  borderBottom: activeTab === tab ? '2px solid #1a2533' : '2px solid transparent',
                  color: activeTab === tab ? '#1a2533' : '#6b7280',
                }}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          <div style={{ overflow: 'auto', maxHeight: 500 }}>
            {activeTab === 'users' && (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {['Username', 'Status', 'Profile', 'Default TS', 'Created', 'Last Login'].map((h) => (
                      <th key={h} style={thStyle}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.username} style={{ ':hover': { background: '#f9fafb' } } as any}>
                      <td style={tdStyle}><strong>{u.username}</strong></td>
                      <td style={tdStyle}>
                        <span style={{
                          background: u.account_status === 'OPEN' ? '#d1fae5' : '#fee2e2',
                          color: u.account_status === 'OPEN' ? '#065f46' : '#991b1b',
                          padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem',
                        }}>
                          {u.account_status}
                        </span>
                      </td>
                      <td style={tdStyle}>{u.profile}</td>
                      <td style={tdStyle}>{u.default_tablespace}</td>
                      <td style={tdStyle}>{u.created}</td>
                      <td style={tdStyle}>{u.last_login || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'roles' && (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {['Role', 'Password Required', 'Auth Type', 'Common', 'Oracle Maintained'].map((h) => (
                      <th key={h} style={thStyle}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {roles.map((r) => (
                    <tr key={r.role}>
                      <td style={tdStyle}><strong>{r.role}</strong></td>
                      <td style={tdStyle}>{r.password_required}</td>
                      <td style={tdStyle}>{r.authentication_type || '—'}</td>
                      <td style={tdStyle}>{r.common}</td>
                      <td style={tdStyle}>{r.oracle_maintained}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
