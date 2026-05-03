/**
 * Triage / declutter API.
 */

import { get, post } from './client';
import type { ItemImage, OwnerInfo, PathElement, Tag } from '$lib/types';

export type TriageDecision = 'love' | 'undecided' | 'hate';

export interface TriageNextItem {
	id: string;
	name: string;
	description: string | null;
	size: string | null;
	primary_image_url: string | null;
	images: ItemImage[];
	tags: Tag[];
	owner: OwnerInfo | null;
	path: PathElement[];
	previous_decision: TriageDecision | null;
	previous_decided_at: string | null;
}

export interface TriageNextResponse {
	item: TriageNextItem | null;
	remaining_estimate: number;
}

export interface TriageFilterOption {
	id: string;
	label: string;
	count: number;
}

export interface TriageFiltersResponse {
	owners: TriageFilterOption[];
	tags: TriageFilterOption[];
}

export interface DiscardItem {
	id: string;
	name: string;
	size: string | null;
	primary_image_url: string | null;
	owner: OwnerInfo | null;
	decided_at: string | null;
}

export interface DiscardGroup {
	container_id: string;
	path_label: string;
	items: DiscardItem[];
}

export interface DiscardResponse {
	groups: DiscardGroup[];
	total: number;
}

export async function next(options?: {
	ownerId?: string;
	tag?: string;
}): Promise<TriageNextResponse> {
	const params = new URLSearchParams();
	if (options?.ownerId) params.set('owner_id', options.ownerId);
	if (options?.tag) params.set('tag', options.tag);
	const qs = params.toString();
	return get<TriageNextResponse>(qs ? `/triage/next?${qs}` : '/triage/next');
}

export async function decide(itemId: string, decision: TriageDecision): Promise<void> {
	await post(`/triage/${itemId}/decide`, { decision });
}

export async function undo(itemId: string): Promise<void> {
	await post(`/triage/${itemId}/undo`, {});
}

export async function markDonated(itemId: string): Promise<void> {
	await post(`/triage/${itemId}/mark-donated`, {});
}

export async function filters(): Promise<TriageFiltersResponse> {
	return get<TriageFiltersResponse>('/triage/filters');
}

export async function discardList(): Promise<DiscardResponse> {
	return get<DiscardResponse>('/triage/discard');
}
