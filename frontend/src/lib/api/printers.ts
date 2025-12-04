/**
 * Printers API client for StorageHub.
 */

import { get, post, patch, del } from './client';
import type { Printer, PrinterCreate, PrinterUpdate, PrintResult } from '$lib/types';

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
	includeContents: boolean = false
): Promise<PrintResult> {
	return post<PrintResult>(`/printers/${printerId}/print`, {
		container_id: containerId,
		include_contents: includeContents
	});
}

/**
 * Get label preview URL for a container.
 */
export function getPreviewUrl(
	printerId: string,
	containerId: string,
	includeContents: boolean = false
): string {
	const params = new URLSearchParams({
		container_id: containerId,
		include_contents: String(includeContents)
	});
	return `/api/printers/${printerId}/preview?${params.toString()}`;
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
