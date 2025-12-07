/**
 * Search API functions.
 */

import { get } from './client';
import type { Condition, Seasonal, PathElement, Item } from '$lib/types';

export interface SearchResultItem extends Item {
	path: PathElement[];
	thumbnail_url: string | null;
	matching_tags: string[];
}

export interface SearchResult {
	query: string | null;
	total: number;
	items: SearchResultItem[];
}

export interface SearchFilters {
	q?: string;
	owner?: string;
	location?: string;
	container?: string;
	size?: string;
	condition?: Condition;
	seasonal?: Seasonal;
	tags?: string[];
	limit?: number;
	offset?: number;
}

export async function searchItems(filters: SearchFilters): Promise<SearchResult> {
	const params = new URLSearchParams();

	if (filters.q) params.set('q', filters.q);
	if (filters.owner) params.set('owner', filters.owner);
	if (filters.location) params.set('location', filters.location);
	if (filters.container) params.set('container', filters.container);
	if (filters.size) params.set('size', filters.size);
	if (filters.condition) params.set('condition', filters.condition);
	if (filters.seasonal) params.set('seasonal', filters.seasonal);
	if (filters.tags && filters.tags.length > 0) params.set('tags', filters.tags.join(','));
	if (filters.limit) params.set('limit', filters.limit.toString());
	if (filters.offset) params.set('offset', filters.offset.toString());

	const queryString = params.toString();
	return get<SearchResult>(`/search${queryString ? `?${queryString}` : ''}`);
}

export async function autocomplete(query: string, limit = 8): Promise<SearchResult> {
	const params = new URLSearchParams({ q: query, limit: limit.toString() });
	return get<SearchResult>(`/search/autocomplete?${params.toString()}`);
}
