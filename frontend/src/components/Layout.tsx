import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  width: 220,
  minHeight: '100vh',
  background: '#1a2533',
  padding: '1.5rem 0',
  color: '#fff',
  flexShrink: 0,
};

const linkStyle: React.CSSProperties = {
  color: '#b0bec5',
  textDecoration: 'none',
  padding: '0.6rem 1.5rem',
  display: 'block',
  fontSize: '0.9rem',
};

const activeLinkStyle: React.CSSProperties = {
  ...linkStyle,
  color: '#fff',
  background: '#2d3f55',
  borderLeft: '3px solid #4CAF50',
};

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <nav style={navStyle}>
        <div style={{ padding: '0 1.5rem 1.5rem', borderBottom: '1px solid #2d3f55' }}>
          <h1 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', lineHeight: 1.3 }}>
            Oracle Access<br />Governance
          </h1>
        </div>
        <div style={{ marginTop: '1rem', flex: 1 }}>
          <NavLink
            to="/"
            end
            style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}
          >
            📊 Dashboard
          </NavLink>
          <NavLink
            to="/inventory"
            style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}
          >
            🗄️ Inventory
          </NavLink>
          <NavLink
            to="/requests"
            style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}
          >
            📋 My Requests
          </NavLink>
          {(user?.role === 'admin' || user?.role === 'approver') && (
            <NavLink
              to="/approvals"
              style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}
            >
              ✅ Approval Queue
            </NavLink>
          )}
          <NavLink
            to="/audit"
            style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}
          >
            🔍 Audit Log
          </NavLink>
          {user?.role === 'admin' && (
            <NavLink
              to="/users"
              style={({ isActive }) => isActive ? activeLinkStyle : linkStyle}
            >
              👥 Users
            </NavLink>
          )}
        </div>
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #2d3f55' }}>
          <div style={{ fontSize: '0.8rem', color: '#b0bec5', marginBottom: '0.5rem' }}>
            {user?.full_name}<br />
            <span style={{ background: '#2d3f55', padding: '2px 6px', borderRadius: 3, fontSize: '0.75rem' }}>
              {user?.role}
            </span>
          </div>
          <button
            onClick={logout}
            style={{
              background: 'none', border: '1px solid #b0bec5', color: '#b0bec5',
              padding: '0.3rem 0.8rem', borderRadius: 4, cursor: 'pointer', fontSize: '0.8rem',
            }}
          >
            Logout
          </button>
        </div>
      </nav>
      <main style={{ flex: 1, padding: '2rem', overflow: 'auto' }}>
        <Outlet />
      </main>
    </div>
  );
}
