/**
 * Outgrown items API.
 */

import { get } from './client';
import type { OwnerInfo } from '$lib/types';

export interface OutgrownInheritCandidate {
	user: OwnerInfo;
	user_age_months: number;
	months_until_fit: number;
}

export interface OutgrownItem {
	id: string;
	name: string;
	size: string | null;
	primary_image_url: string | null;
	container_id: string;
	effective_owner: OwnerInfo;
	is_suggested_owner: boolean;
	effective_owner_age_months: number;
	size_age_min_months: number;
	size_age_max_months: number;
	months_outgrown: number;
	inherit_to: OutgrownInheritCandidate | null;
}

export interface OutgrownResponse {
	items: OutgrownItem[];
}

export async function listOutgrown(): Promise<OutgrownResponse> {
	return get<OutgrownResponse>('/outgrown');
}
