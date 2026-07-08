import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { AppUser } from '../types';

export default function UsersPage() {
  const [users, setUsers] = useState<AppUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', full_name: '', role: 'requester', password: '' });
  const [error, setError] = useState('');

  const loadUsers = () => {
    api.get<AppUser[]>('/users')
      .then((r) => setUsers(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadUsers(); }, []);

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/users', form);
      setShowForm(false);
      setForm({ username: '', email: '', full_name: '', role: 'requester', password: '' });
      loadUsers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const toggleActive = async (user: AppUser) => {
    await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
    loadUsers();
  };

  const thStyle: React.CSSProperties = {
    textAlign: 'left', padding: '0.6rem 0.75rem', fontSize: '0.75rem',
    fontWeight: 600, color: '#6b7280', textTransform: 'uppercase',
    background: '#f9fafb', borderBottom: '1px solid #e5e7eb',
  };
  const tdStyle: React.CSSProperties = {
    padding: '0.6rem 0.75rem', fontSize: '0.875rem', borderBottom: '1px solid #f3f4f6',
  };
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: 4, fontSize: '0.875rem',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Application Users</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{ background: '#1a2533', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
        >
          + New User
        </button>
      </div>

      {showForm && (
        <div style={{ background: '#fff', borderRadius: 8, padding: '1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.5rem', maxWidth: 600 }}>
          <h3 style={{ marginBottom: '1rem' }}>Create Application User</h3>
          {error && <div style={{ color: '#dc2626', marginBottom: '0.75rem', fontSize: '0.875rem' }}>{error}</div>}
          <form onSubmit={createUser} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            {[
              { name: 'username', label: 'Username' },
              { name: 'email', label: 'Email' },
              { name: 'full_name', label: 'Full Name' },
              { name: 'password', label: 'Password', type: 'password' },
            ].map(({ name, label, type = 'text' }) => (
              <div key={name}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 4 }}>{label}</label>
                <input
                  type={type}
                  value={(form as any)[name]}
                  onChange={(e) => setForm({ ...form, [name]: e.target.value })}
                  required
                  style={inputStyle}
                />
              </div>
            ))}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 4 }}>Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                style={inputStyle}
              >
                {['admin', 'approver', 'requester', 'auditor'].map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '0.75rem' }}>
              <button type="submit" style={{ background: '#1a2533', color: '#fff', border: 'none', padding: '0.5rem 1rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}>
                Create
              </button>
              <button type="button" onClick={() => setShowForm(false)} style={{ background: '#f3f4f6', color: '#374151', border: 'none', padding: '0.5rem 1rem', borderRadius: 4, cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Username', 'Full Name', 'Email', 'Role', 'Active', 'Created', 'Actions'].map((h) => (
                <th key={h} style={thStyle}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td style={tdStyle}><strong>{u.username}</strong></td>
                <td style={tdStyle}>{u.full_name}</td>
                <td style={tdStyle}>{u.email}</td>
                <td style={tdStyle}>
                  <span style={{ background: '#e0e7ff', color: '#3730a3', padding: '2px 8px', borderRadius: 12, fontSize: '0.75rem' }}>
                    {u.role}
                  </span>
                </td>
                <td style={tdStyle}>
                  <span style={{ color: u.is_active ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                    {u.is_active ? 'Yes' : 'No'}
                  </span>
                </td>
                <td style={tdStyle}>{new Date(u.created_at).toLocaleDateString()}</td>
                <td style={tdStyle}>
                  <button
                    onClick={() => toggleActive(u)}
                    style={{ background: u.is_active ? '#fee2e2' : '#d1fae5', color: u.is_active ? '#dc2626' : '#065f46', border: 'none', padding: '0.25rem 0.6rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.8rem' }}
                  >
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <p style={{ padding: '1rem', color: '#6b7280' }}>Loading…</p>}
      </div>
    </div>
  );
}
