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

export type DeleteMode = 'fail' | 'recursive' | 'transfer';

export interface DeleteContainerOptions {
	mode?: DeleteMode;
	transferTo?: string;
}

export async function deleteContainer(id: string, options?: DeleteContainerOptions): Promise<void> {
	const params = new URLSearchParams();
	if (options?.mode) {
		params.append('mode', options.mode);
	}
	if (options?.transferTo) {
		params.append('transfer_to', options.transferTo);
	}
	const queryString = params.toString();
	return del(`/containers/${id}${queryString ? `?${queryString}` : ''}`);
}

export function getContainerQRUrl(id: string): string {
	return `/api/containers/${id}/qr`;
}
