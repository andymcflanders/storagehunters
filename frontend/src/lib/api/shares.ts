/**
 * Share links API client.
 */

import { get, post, patch, del } from './client';

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
	image_url: string | null;
}

export interface PublicShareResponse {
	container: PublicContainer;
	items: PublicItem[] | null;
}

export async function createShareLink(data: CreateShareLinkRequest): Promise<ShareLink> {
	return post<ShareLink>('/shares', data);
}

export async function listShareLinks(containerId?: string): Promise<ShareLinkListResponse> {
	const params = new URLSearchParams();
	if (containerId) {
		params.set('container_id', containerId);
	}
	const url = params.toString() ? `/shares?${params}` : '/shares';
	return get<ShareLinkListResponse>(url);
}

export async function deleteShareLink(shareId: string): Promise<void> {
	return del(`/shares/${shareId}`);
}

export async function toggleShareLink(shareId: string): Promise<ShareLink> {
	return patch<ShareLink>(`/shares/${shareId}/toggle`, {});
}

export async function getPublicShare(token: string): Promise<PublicShareResponse> {
	return get<PublicShareResponse>(`/shares/public/${token}`);
}
