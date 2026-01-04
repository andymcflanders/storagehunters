/**
 * Printers API client for StorageHub.
 */

import { get, post, patch, del } from './client';
import type {
	Printer,
	PrinterCreate,
	PrinterUpdate,
	PrintResult,
	LabelTemplate,
	MediaSuggestion,
	BatchPrintResult
} from '$lib/types';

/**
 * Get all printers.
 */
export async function getPrinters(): Promise<Printer[]> {
	return get<Printer[]>('/printers');
}

/**
 * Get a single printer by ID.
 */
export async function getPrinter(id: string): Promise<Printer> {
	return get<Printer>(`/printers/${id}`);
}

/**
 * Create a new printer.
 */
export async function createPrinter(data: PrinterCreate): Promise<Printer> {
	return post<Printer>('/printers', data);
}

/**
 * Update a printer.
 */
export async function updatePrinter(id: string, data: PrinterUpdate): Promise<Printer> {
	return patch<Printer>(`/printers/${id}`, data);
}

/**
 * Delete a printer.
 */
export async function deletePrinter(id: string): Promise<void> {
	return del<void>(`/printers/${id}`);
}

/**
 * Test printer connection.
 */
export async function testPrinter(id: string): Promise<PrintResult> {
	return post<PrintResult>(`/printers/${id}/test`);
}

/**
 * Print a label for a container.
 */
export async function printLabel(
	printerId: string,
	containerId: string,
	template: LabelTemplate = 'qr_only',
	includeContents: boolean = false
): Promise<PrintResult> {
	return post<PrintResult>(`/printers/${printerId}/print`, {
		container_id: containerId,
		template,
		include_contents: includeContents
	});
}

/**
 * Get label preview URL for a container.
 */
export function getPreviewUrl(
	printerId: string,
	containerId: string,
	template: LabelTemplate = 'qr_only',
	includeContents: boolean = false
): string {
	const params = new URLSearchParams({
		container_id: containerId,
		template,
		include_contents: String(includeContents)
	});
	return `/api/printers/${printerId}/preview?${params.toString()}`;
}

/**
 * Detect media loaded in printer and get template suggestion.
 */
export async function detectMedia(printerId: string): Promise<MediaSuggestion> {
	return get<MediaSuggestion>(`/printers/${printerId}/media`);
}

/**
 * Print labels for multiple containers.
 */
export async function printBatch(
	printerId: string,
	containerIds: string[],
	template: LabelTemplate = 'qr_only'
): Promise<BatchPrintResult> {
	return post<BatchPrintResult>(`/printers/${printerId}/print-batch`, {
		container_ids: containerIds,
		template
	});
}

/**
 * Get batch labels PDF URL.
 */
export function getBatchPdfUrl(containerIds: string[], layout: string = 'avery_5160'): string {
	const params = new URLSearchParams();
	containerIds.forEach((id) => params.append('container_ids', id));
	params.append('layout', layout);
	return `/api/printers/batch-pdf?${params.toString()}`;
}

/**
 * Get download URL for a single label PDF.
 */
export function getDownloadUrl(
	printerId: string,
	containerId: string,
	template: LabelTemplate = 'qr_only'
): string {
	const params = new URLSearchParams({
		container_id: containerId,
		template
	});
	return `/api/printers/${printerId}/download?${params.toString()}`;
}
