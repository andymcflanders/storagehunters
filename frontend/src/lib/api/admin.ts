/**
 * Admin API client.
 */

import { get, post, patch, del } from './client';

export type UserRole = 'admin' | 'user';

export interface SystemStats {
	total_users: number;
	active_users: number;
	admin_users: number;
	total_locations: number;
	total_containers: number;
	total_items: number;
	recent_activity_count: number;
	users_created_last_30_days: number;
	items_created_last_30_days: number;
}

export interface AdminUser {
	id: string;
	name: string;
	email: string | null;
	role: UserRole;
	is_active: boolean;
	requires_password: boolean;
	created_at: string;
	updated_at: string;
	item_count: number;
	last_activity: string | null;
}

export interface UserListResponse {
	items: AdminUser[];
	total: number;
	page: number;
	page_size: number;
}

export interface CreateUserRequest {
	name: string;
	email?: string | null;
	role?: UserRole;
	requires_password?: boolean;
	password?: string | null;
}

export interface UpdateUserRequest {
	name?: string;
	email?: string | null;
	role?: UserRole;
	is_active?: boolean;
	requires_password?: boolean;
	password?: string | null;
}

export interface ActivityLogItem {
	id: string;
	user_id: string | null;
	user_name: string | null;
	action: string;
	entity_type: string;
	entity_id: string;
	entity_name: string;
	details: Record<string, unknown> | null;
	created_at: string;
}

export interface ActivityLogResponse {
	items: ActivityLogItem[];
	total: number;
	page: number;
	page_size: number;
}

export interface UserListFilters {
	page?: number;
	page_size?: number;
	search?: string;
	role?: UserRole;
	is_active?: boolean;
}

export interface ActivityLogFilters {
	page?: number;
	page_size?: number;
	user_id?: string;
	action?: string;
	entity_type?: string;
	days?: number;
}

export async function getSystemStats(): Promise<SystemStats> {
	return get<SystemStats>('/admin/stats');
}

export async function listUsers(filters: UserListFilters = {}): Promise<UserListResponse> {
	const params = new URLSearchParams();
	if (filters.page) params.set('page', filters.page.toString());
	if (filters.page_size) params.set('page_size', filters.page_size.toString());
	if (filters.search) params.set('search', filters.search);
	if (filters.role) params.set('role', filters.role);
	if (filters.is_active !== undefined) params.set('is_active', filters.is_active.toString());

	const url = params.toString() ? `/admin/users?${params}` : '/admin/users';
	return get<UserListResponse>(url);
}

export async function createUser(data: CreateUserRequest): Promise<AdminUser> {
	return post<AdminUser>('/admin/users', data);
}

export async function updateUser(userId: string, data: UpdateUserRequest): Promise<AdminUser> {
	return patch<AdminUser>(`/admin/users/${userId}`, data);
}

export async function deleteUser(userId: string): Promise<void> {
	return del(`/admin/users/${userId}`);
}

export async function getActivityLogs(filters: ActivityLogFilters = {}): Promise<ActivityLogResponse> {
	const params = new URLSearchParams();
	if (filters.page) params.set('page', filters.page.toString());
	if (filters.page_size) params.set('page_size', filters.page_size.toString());
	if (filters.user_id) params.set('user_id', filters.user_id);
	if (filters.action) params.set('action', filters.action);
	if (filters.entity_type) params.set('entity_type', filters.entity_type);
	if (filters.days) params.set('days', filters.days.toString());

	const url = params.toString() ? `/admin/activity?${params}` : '/admin/activity';
	return get<ActivityLogResponse>(url);
}

// OpenAI settings

export interface ModelOption {
	id: string;
	name: string;
	description: string;
}

export interface CostEstimate {
	model: string;
	estimated_input_tokens: number;
	estimated_output_tokens: number;
	estimated_cost_usd: number;
	cost_per_image_usd?: number;
}

export interface OpenAISettings {
	vision_enabled: boolean;
	vision_model: string;
	vision_max_tokens: number;
	vision_temperature: number;
	vision_cost_estimate: CostEstimate;

	summary_enabled: boolean;
	summary_model: string;
	summary_max_tokens: number;
	summary_temperature: number;
	summary_cost_estimate: CostEstimate;

	vision_models: ModelOption[];
	text_models: ModelOption[];

	api_key_set: boolean;
}

export interface OpenAISettingsUpdate {
	vision_enabled?: boolean;
	vision_model?: string;
	vision_max_tokens?: number;
	vision_temperature?: number;

	summary_enabled?: boolean;
	summary_model?: string;
	summary_max_tokens?: number;
	summary_temperature?: number;
}

export async function getOpenAISettings(): Promise<OpenAISettings> {
	return get<OpenAISettings>('/admin/openai');
}

export async function updateOpenAISettings(data: OpenAISettingsUpdate): Promise<OpenAISettings> {
	const response = await fetch('/api/admin/openai', {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data),
		credentials: 'include'
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Update failed' }));
		throw new Error(error.detail || 'Update failed');
	}

	return response.json();
}
