/**
 * Locations API functions.
 */

import { get, post, patch, del } from './client';
import type { Location, LocationWithContainers, LocationCreate, LocationUpdate } from '$lib/types';

export async function listLocations(): Promise<Location[]> {
	return get<Location[]>('/locations');
}

export async function createLocation(data: LocationCreate): Promise<Location> {
	return post<Location>('/locations', data);
}

export async function getLocation(id: string): Promise<LocationWithContainers> {
	return get<LocationWithContainers>(`/locations/${id}`);
}

export async function updateLocation(id: string, data: LocationUpdate): Promise<Location> {
	return patch<Location>(`/locations/${id}`, data);
}

export async function deleteLocation(id: string): Promise<void> {
	return del(`/locations/${id}`);
}
