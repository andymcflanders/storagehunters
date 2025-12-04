/**
 * Share links API client.
 */

import { apiClient } from './client';

export interface ShareLink {
	id: string;
	container_id: string;
	token: string;
	is_active: boolean;
	allow_item_view: boolean;
	expires_at: string | null;
	created_at: string;
	view_count: number;
	share_url: string;
}

export interface ShareLinkListResponse {
	items: ShareLink[];
	total: number;
}

export interface CreateShareLinkRequest {
	container_id: string;
	allow_item_view?: boolean;
	expires_in_days?: number | null;
}

export interface PublicContainer {
	id: string;
	name: string;
	notes: string | null;
	location_name: string;
	item_count: number;
}

export interface PublicItem {
	id: string;
	name: string;
	description: string | null;
	quantity: number;
	image_url: string | null;
}

export interface PublicShareResponse {
	container: PublicContainer;
	items: PublicItem[] | null;
}

export async function createShareLink(data: CreateShareLinkRequest): Promise<ShareLink> {
	const response = await apiClient('/api/shares', {
		method: 'POST',
		body: JSON.stringify(data)
	});
	return response.json();
}

export async function listShareLinks(containerId?: string): Promise<ShareLinkListResponse> {
	const params = new URLSearchParams();
	if (containerId) {
		params.set('container_id', containerId);
	}
	const url = params.toString() ? `/api/shares?${params}` : '/api/shares';
	const response = await apiClient(url);
	return response.json();
}

export async function deleteShareLink(shareId: string): Promise<void> {
	await apiClient(`/api/shares/${shareId}`, {
		method: 'DELETE'
	});
}

export async function toggleShareLink(shareId: string): Promise<ShareLink> {
	const response = await apiClient(`/api/shares/${shareId}/toggle`, {
		method: 'PATCH'
	});
	return response.json();
}

export async function getPublicShare(token: string): Promise<PublicShareResponse> {
	const response = await fetch(`/api/shares/public/${token}`);
	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || 'Failed to load share');
	}
	return response.json();
}
