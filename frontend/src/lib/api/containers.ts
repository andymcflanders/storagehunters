/**
 * Containers API functions.
 */

import { get, post, patch, del } from './client';
import type { Container, ContainerWithItems, ContainerCreate, ContainerUpdate } from '$lib/types';

export async function listContainers(locationId?: string): Promise<Container[]> {
	const params = locationId ? `?location_id=${locationId}` : '';
	return get<Container[]>(`/containers${params}`);
}

export async function createContainer(data: ContainerCreate): Promise<Container> {
	return post<Container>('/containers', data);
}

export async function getContainer(id: string): Promise<ContainerWithItems> {
	return get<ContainerWithItems>(`/containers/${id}`);
}

export async function getContainerByQR(qrCode: string): Promise<ContainerWithItems> {
	return get<ContainerWithItems>(`/containers/qr/${qrCode}`);
}

export async function updateContainer(id: string, data: ContainerUpdate): Promise<Container> {
	return patch<Container>(`/containers/${id}`, data);
}

export async function deleteContainer(id: string): Promise<void> {
	return del(`/containers/${id}`);
}

export function getContainerQRUrl(id: string): string {
	return `/api/containers/${id}/qr`;
}
