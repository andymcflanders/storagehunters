/**
 * Uploads API functions for segmentation-based item creation.
 */

import { get, post } from './client';
import type { PendingUpload, PendingUploadWithItems } from '$lib/types';

interface BatchUploadResponse {
	pending_uploads: PendingUpload[];
}

/**
 * Upload images to a container for segmentation processing.
 * Each detected object becomes a separate Item.
 */
export async function uploadToContainer(
	containerId: string,
	files: File[],
	multiItemMode: boolean = false
): Promise<PendingUpload[]> {
	const formData = new FormData();
	for (const file of files) {
		formData.append('files', file);
	}
	formData.append('multi_item_mode', String(multiItemMode));

	const response = await fetch(`/api/uploads/containers/${containerId}/upload`, {
		method: 'POST',
		body: formData,
		credentials: 'include'
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
		throw new Error(error.detail || 'Upload failed');
	}

	const data: BatchUploadResponse = await response.json();
	return data.pending_uploads;
}

/**
 * Get all pending uploads for the current user.
 */
export async function getPendingUploads(): Promise<PendingUpload[]> {
	return get<PendingUpload[]>('/uploads/pending');
}

/**
 * Get status of a specific pending upload.
 */
export async function getPendingUpload(uploadId: string): Promise<PendingUploadWithItems> {
	return get<PendingUploadWithItems>(`/uploads/pending/${uploadId}`);
}
