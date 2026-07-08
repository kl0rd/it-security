import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { RequestType } from '../types';

const REQUEST_TYPES: { value: RequestType; label: string }[] = [
  { value: 'create_user', label: 'Create User' },
  { value: 'drop_user', label: 'Drop User' },
  { value: 'lock_user', label: 'Lock User' },
  { value: 'unlock_user', label: 'Unlock User' },
  { value: 'grant_role', label: 'Grant Role' },
  { value: 'revoke_role', label: 'Revoke Role' },
  { value: 'grant_system_privilege', label: 'Grant System Privilege' },
  { value: 'revoke_system_privilege', label: 'Revoke System Privilege' },
  { value: 'grant_object_privilege', label: 'Grant Object Privilege' },
  { value: 'revoke_object_privilege', label: 'Revoke Object Privilege' },
];

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.5rem', border: '1px solid #d1d5db',
  borderRadius: 4, fontSize: '0.875rem',
};
const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: '0.8rem', fontWeight: 500, marginBottom: 4,
};
const fieldStyle: React.CSSProperties = { marginBottom: '1rem' };

function ParameterFields({ type, params, onChange }: {
  type: RequestType;
  params: Record<string, string>;
  onChange: (k: string, v: string) => void;
}) {
  const field = (name: string, label: string, placeholder = '') => (
    <div key={name} style={fieldStyle}>
      <label style={labelStyle}>{label}</label>
      <input
        value={params[name] || ''}
        onChange={(e) => onChange(name, e.target.value)}
        placeholder={placeholder}
        style={inputStyle}
      />
    </div>
  );

  switch (type) {
    case 'create_user':
      return (
        <>
          {field('username', 'Oracle Username *', 'JOHN_DOE')}
          {field('profile', 'Profile', 'DEFAULT')}
          {field('default_tablespace', 'Default Tablespace', 'USERS')}
          {field('temporary_tablespace', 'Temporary Tablespace', 'TEMP')}
        </>
      );
    case 'drop_user':
      return (
        <>
          {field('username', 'Oracle Username *', 'JOHN_DOE')}
          <div style={fieldStyle}>
            <label style={labelStyle}>Cascade (drop owned objects)</label>
            <select
              value={params['cascade'] || 'true'}
              onChange={(e) => onChange('cascade', e.target.value)}
              style={inputStyle}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
        </>
      );
    case 'lock_user':
    case 'unlock_user':
      return field('username', 'Oracle Username *', 'JOHN_DOE');
    case 'grant_role':
    case 'revoke_role':
      return (
        <>
          {field('grantee', 'Grantee (user or role) *', 'JOHN_DOE')}
          {field('role', 'Role Name *', 'DBA')}
          {type === 'grant_role' && (
            <div style={fieldStyle}>
              <label style={labelStyle}>With Admin Option</label>
              <select
                value={params['admin_option'] || 'false'}
                onChange={(e) => onChange('admin_option', e.target.value)}
                style={inputStyle}
              >
                <option value="false">No</option>
                <option value="true">Yes</option>
              </select>
            </div>
          )}
        </>
      );
    case 'grant_system_privilege':
    case 'revoke_system_privilege':
      return (
        <>
          {field('grantee', 'Grantee *', 'JOHN_DOE')}
          {field('privilege', 'System Privilege *', 'CREATE SESSION')}
          {type === 'grant_system_privilege' && (
            <div style={fieldStyle}>
              <label style={labelStyle}>With Admin Option</label>
              <select
                value={params['admin_option'] || 'false'}
                onChange={(e) => onChange('admin_option', e.target.value)}
                style={inputStyle}
              >
                <option value="false">No</option>
                <option value="true">Yes</option>
              </select>
            </div>
          )}
        </>
      );
    case 'grant_object_privilege':
    case 'revoke_object_privilege':
      return (
        <>
          {field('grantee', 'Grantee *', 'JOHN_DOE')}
          {field('privilege', 'Object Privilege *', 'SELECT')}
          {field('object_owner', 'Object Owner *', 'HR')}
          {field('object_name', 'Object Name *', 'EMPLOYEES')}
          {type === 'grant_object_privilege' && (
            <div style={fieldStyle}>
              <label style={labelStyle}>With Grant Option</label>
              <select
                value={params['grant_option'] || 'false'}
                onChange={(e) => onChange('grant_option', e.target.value)}
                style={inputStyle}
              >
                <option value="false">No</option>
                <option value="true">Yes</option>
              </select>
            </div>
          )}
        </>
      );
    default:
      return null;
  }
}

export default function NewRequestPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [requestType, setRequestType] = useState<RequestType>('grant_role');
  const [host, setHost] = useState('');
  const [port, setPort] = useState('1521');
  const [service, setService] = useState('');
  const [pdb, setPdb] = useState('');
  const [params, setParams] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const updateParam = (k: string, v: string) => setParams((p) => ({ ...p, [k]: v }));

  const handleSubmit = async (e: React.FormEvent, submit = false) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Convert boolean-like strings to actual booleans
    const cleanedParams: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(params)) {
      if (v === 'true') cleanedParams[k] = true;
      else if (v === 'false') cleanedParams[k] = false;
      else cleanedParams[k] = v;
    }

    try {
      const res = await api.post('/requests', {
        title,
        description,
        request_type: requestType,
        target_db_host: host,
        target_db_port: parseInt(port),
        target_db_service: service,
        target_pdb: pdb || undefined,
        parameters: cleanedParams,
      });
      const reqId = res.data.id;
      if (submit) {
        await api.post(`/requests/${reqId}/submit`);
      }
      navigate(`/requests/${reqId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>New Access Request</h2>
      <div style={{ background: '#fff', borderRadius: 8, padding: '2rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', maxWidth: 700 }}>
        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#dc2626', padding: '0.75rem', borderRadius: 4, marginBottom: '1rem', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}
        <form onSubmit={(e) => handleSubmit(e, false)}>
          {/* Basic info */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Title *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required style={inputStyle} />
          </div>
          <div style={fieldStyle}>
            <label style={labelStyle}>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>
          <div style={fieldStyle}>
            <label style={labelStyle}>Request Type *</label>
            <select
              value={requestType}
              onChange={(e) => { setRequestType(e.target.value as RequestType); setParams({}); }}
              style={inputStyle}
            >
              {REQUEST_TYPES.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {/* Target database */}
          <h4 style={{ marginBottom: '0.75rem', color: '#374151' }}>Target Database</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={fieldStyle}>
              <label style={labelStyle}>Host *</label>
              <input value={host} onChange={(e) => setHost(e.target.value)} required style={inputStyle} placeholder="oracle.example.com" />
            </div>
            <div style={fieldStyle}>
              <label style={labelStyle}>Port *</label>
              <input value={port} onChange={(e) => setPort(e.target.value)} required style={inputStyle} />
            </div>
            <div style={fieldStyle}>
              <label style={labelStyle}>Service Name *</label>
              <input value={service} onChange={(e) => setService(e.target.value)} required style={inputStyle} placeholder="ORCLPDB1" />
            </div>
            <div style={fieldStyle}>
              <label style={labelStyle}>PDB (optional)</label>
              <input value={pdb} onChange={(e) => setPdb(e.target.value)} style={inputStyle} placeholder="MYPDB" />
            </div>
          </div>

          {/* Request-specific parameters */}
          <h4 style={{ marginBottom: '0.75rem', color: '#374151' }}>Request Parameters</h4>
          <ParameterFields type={requestType} params={params} onChange={updateParam} />

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
            <button
              type="submit"
              disabled={loading}
              style={{
                background: '#6b7280', color: '#fff', border: 'none',
                padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600,
              }}
            >
              Save as Draft
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={(e) => handleSubmit(e as any, true)}
              style={{
                background: '#1a2533', color: '#fff', border: 'none',
                padding: '0.6rem 1.2rem', borderRadius: 4, cursor: 'pointer', fontWeight: 600,
              }}
            >
              {loading ? 'Saving…' : 'Submit for Approval'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
