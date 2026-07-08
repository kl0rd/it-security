import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '100vh', background: '#f5f7fa',
    }}>
      <div style={{
        background: '#fff', padding: '2.5rem', borderRadius: 8,
        boxShadow: '0 2px 12px rgba(0,0,0,0.1)', width: 360,
      }}>
        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: '#1a2533' }}>
          Oracle Access Governance
        </h1>
        <p style={{ color: '#666', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          Sign in with your credentials
        </p>
        {error && (
          <div style={{
            background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626',
            padding: '0.75rem', borderRadius: 4, marginBottom: '1rem', fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.875rem', fontWeight: 500 }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: '100%', padding: '0.6rem', border: '1px solid #d1d5db',
                borderRadius: 4, fontSize: '0.9rem',
              }}
            />
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.4rem', fontSize: '0.875rem', fontWeight: 500 }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%', padding: '0.6rem', border: '1px solid #d1d5db',
                borderRadius: 4, fontSize: '0.9rem',
              }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '0.75rem', background: '#1a2533',
              color: '#fff', border: 'none', borderRadius: 4, fontSize: '0.9rem',
              cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 600,
            }}
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
