/**
 * Items API functions.
 */

import { get, post, patch, del, upload } from './client';
import type { Item, ItemWithDetails, ItemCreate, ItemUpdate, ItemImage, Tag } from '$lib/types';

export async function listItems(containerId?: string, ownerId?: string): Promise<Item[]> {
	const params = new URLSearchParams();
	if (containerId) params.set('container_id', containerId);
	if (ownerId) params.set('owner_id', ownerId);
	const queryString = params.toString();
	return get<Item[]>(`/items${queryString ? `?${queryString}` : ''}`);
}

export async function createItem(data: ItemCreate): Promise<Item> {
	return post<Item>('/items', data);
}

export async function getItem(id: string): Promise<ItemWithDetails> {
	return get<ItemWithDetails>(`/items/${id}`);
}

export async function updateItem(id: string, data: ItemUpdate): Promise<Item> {
	return patch<Item>(`/items/${id}`, data);
}

export async function deleteItem(id: string): Promise<void> {
	return del(`/items/${id}`);
}

export async function uploadItemImage(itemId: string, file: File): Promise<ItemImage> {
	return upload<ItemImage>(`/items/${itemId}/images`, file);
}

export async function deleteItemImage(itemId: string, imageId: string): Promise<void> {
	return del(`/items/${itemId}/images/${imageId}`);
}

export async function addItemTag(itemId: string, tagName: string): Promise<Tag> {
	return post<Tag>(`/items/${itemId}/tags?tag_name=${encodeURIComponent(tagName)}`);
}

export async function removeItemTag(itemId: string, tagId: string): Promise<void> {
	return del(`/items/${itemId}/tags/${tagId}`);
}

export async function moveItem(itemId: string, containerId: string): Promise<Item> {
	return post<Item>(`/items/${itemId}/move?container_id=${containerId}`);
}

export async function getPendingReviewItems(): Promise<ItemWithDetails[]> {
	return get<ItemWithDetails[]>('/items/pending-review');
}

export async function confirmItemReview(itemId: string): Promise<Item> {
	return post<Item>(`/items/${itemId}/confirm-review`);
}

export async function setPrimaryImage(itemId: string, imageId: string): Promise<Item> {
	return post<Item>(`/items/${itemId}/images/${imageId}/set-primary`);
}
