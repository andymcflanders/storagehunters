/**
 * Inventory API client for God View.
 */

import { get, post } from './client';
import type { GodViewResponse, ContainerMoveRequest } from '$lib/types';

/**
 * Get the complete inventory tree for God View.
 */
export async function getInventoryTree(): Promise<GodViewResponse> {
	return get<GodViewResponse>('/inventory/tree');
}

/**
 * Move a container to a different location or parent container.
 */
export async function moveContainer(
	containerId: string,
	data: ContainerMoveRequest
): Promise<{ success: boolean; container_id: string; location_id: string; parent_container_id: string | null }> {
	return post(`/inventory/${containerId}/move`, data);
}
