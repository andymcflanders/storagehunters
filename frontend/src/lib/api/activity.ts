/**
 * Activity API client for StorageHub.
 */

import { get } from './client';

export type ActionType = 'created' | 'updated' | 'moved' | 'deleted';

export interface Activity {
	id: string;
	user_id: string | null;
	user_name: string | null;
	action: ActionType;
	entity_type: string;
	entity_id: string;
	entity_name: string;
	details: Record<string, unknown> | null;
	created_at: string;
}

export interface ActivityListResponse {
	items: Activity[];
	total: number;
	page: number;
	page_size: number;
	has_more: boolean;
}

export interface ActivityFilters {
	page?: number;
	page_size?: number;
	entity_type?: string;
	action?: ActionType;
}

/**
 * Get activity log.
 */
export async function getActivities(filters: ActivityFilters = {}): Promise<ActivityListResponse> {
	const params = new URLSearchParams();
	if (filters.page) params.append('page', String(filters.page));
	if (filters.page_size) params.append('page_size', String(filters.page_size));
	if (filters.entity_type) params.append('entity_type', filters.entity_type);
	if (filters.action) params.append('action', filters.action);

	const query = params.toString();
	return get<ActivityListResponse>(`/activity${query ? `?${query}` : ''}`);
}

/**
 * Get current user's activity log.
 */
export async function getMyActivities(
	page: number = 1,
	pageSize: number = 20
): Promise<ActivityListResponse> {
	return get<ActivityListResponse>(`/activity/my?page=${page}&page_size=${pageSize}`);
}
