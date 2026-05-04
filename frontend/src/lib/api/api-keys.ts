/**
 * API Keys management client.
 *
 * Scoped per-user on the backend — list/create/delete operate on the
 * keys owned by whoever's currently logged in. The raw key value is
 * only returned once on creation; storing or retrieving it later is
 * impossible by design.
 */

import { get, post, del } from './client';

export type APIKeyScope = 'read' | 'write' | 'search' | 'webhooks' | 'admin';

export interface APIKeyResponse {
	id: string;
	name: string;
	description: string | null;
	key_prefix: string;
	scopes: string[];
	is_active: boolean;
	last_used_at: string | null;
	expires_at: string | null;
	created_at: string;
}

export interface APIKeyCreatedResponse extends APIKeyResponse {
	/** The raw key value. Only returned once at creation time. */
	key: string;
}

export interface APIKeyCreate {
	name: string;
	description?: string | null;
	scopes: APIKeyScope[];
	expires_at?: string | null;
}

export async function listApiKeys(): Promise<APIKeyResponse[]> {
	return get<APIKeyResponse[]>('/api-keys');
}

export async function createApiKey(data: APIKeyCreate): Promise<APIKeyCreatedResponse> {
	return post<APIKeyCreatedResponse>('/api-keys', data);
}

export async function deleteApiKey(keyId: string): Promise<void> {
	await del(`/api-keys/${keyId}`);
}
