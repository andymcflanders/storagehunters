/**
 * Tags API functions.
 */

import { get, post, patch, del } from './client';
import type { Tag } from '$lib/types';

export interface TagResponse {
	id: string;
	name: string;
	user_created: boolean;
	created_at: string;
}

export async function listTags(): Promise<TagResponse[]> {
	return get<TagResponse[]>('/tags');
}

export async function createTag(name: string): Promise<TagResponse> {
	return post<TagResponse>('/tags', { name });
}

export async function renameTag(id: string, newName: string): Promise<TagResponse> {
	return patch<TagResponse>(`/tags/${id}?new_name=${encodeURIComponent(newName)}`, {});
}

export async function deleteTag(id: string): Promise<void> {
	return del(`/tags/${id}`);
}

export async function mergeTags(sourceTagIds: string[], targetTagId: string): Promise<TagResponse> {
	return post<TagResponse>('/tags/merge', {
		source_tag_ids: sourceTagIds,
		target_tag_id: targetTagId
	});
}
