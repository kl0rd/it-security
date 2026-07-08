// Domain types mirroring the backend Pydantic schemas

export type AppRole = 'admin' | 'approver' | 'requester' | 'auditor';

export interface AppUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: AppRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type RequestType =
  | 'create_user'
  | 'drop_user'
  | 'lock_user'
  | 'unlock_user'
  | 'grant_role'
  | 'revoke_role'
  | 'grant_system_privilege'
  | 'revoke_system_privilege'
  | 'grant_object_privilege'
  | 'revoke_object_privilege';

export type RequestStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'executed'
  | 'failed'
  | 'rolled_back';

export interface AccessRequest {
  id: number;
  title: string;
  description?: string;
  request_type: RequestType;
  status: RequestStatus;
  target_db_host: string;
  target_db_port: number;
  target_db_service: string;
  target_pdb?: string;
  parameters: Record<string, unknown>;
  execution_sql?: string;
  rollback_sql?: string;
  execution_output?: string;
  execution_error?: string;
  requester_id: number;
  approver_id?: number;
  executor_id?: number;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
  executed_at?: string;
}

export interface AuditLog {
  id: number;
  actor_id?: number;
  actor_username: string;
  action: string;
  access_request_id?: number;
  target_db_host?: string;
  target_db_service?: string;
  target_pdb?: string;
  before_state?: Record<string, unknown>;
  after_state?: Record<string, unknown>;
  sql_executed?: string;
  rollback_sql?: string;
  result?: string;
  success: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export interface OracleUser {
  username: string;
  account_status: string;
  lock_date?: string;
  expiry_date?: string;
  default_tablespace?: string;
  temporary_tablespace?: string;
  profile?: string;
  authentication_type?: string;
  created?: string;
  last_login?: string;
  common?: string;
  oracle_maintained?: string;
}

export interface OracleRole {
  role: string;
  password_required: string;
  authentication_type?: string;
  common?: string;
  oracle_maintained?: string;
}

export interface OracleInventorySummary {
  host: string;
  port: number;
  service_name: string;
  is_cdb: boolean;
  pdbs: { name: string; open_mode: string; restricted?: string; con_id?: number }[];
  user_count: number;
  role_count: number;
  sys_priv_count: number;
  obj_priv_count: number;
  profile_count: number;
}

export interface GeneratedSQL {
  execution_sql: string;
  rollback_sql: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}
