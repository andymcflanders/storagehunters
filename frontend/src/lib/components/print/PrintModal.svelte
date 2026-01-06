<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import type { Printer, LabelTemplate, MediaSuggestion, PrintResult } from '$lib/types';
	import { getPrinters, detectMedia, printLabel, getPreviewUrl, getDownloadUrl } from '$lib/api/printers';
	import TemplateSelector from './TemplateSelector.svelte';
	import MediaInfo from './MediaInfo.svelte';

	export let open = false;
	export let containerId: string;
	export let containerName = '';

	const dispatch = createEventDispatcher<{
		close: void;
		printed: PrintResult;
	}>();

	let printers: Printer[] = [];
	let selectedPrinter: Printer | null = null;
	let selectedTemplate: LabelTemplate = 'qr_only';
	let suggestedTemplate: LabelTemplate | null = null;
	let mediaSuggestion: MediaSuggestion | null = null;
	let loading = true;
	let printing = false;
	let detectingMedia = false;
	let error = '';

	// PDF printers should download instead of print
	$: isPdfPrinter = selectedPrinter?.printer_type === 'generic_pdf';

	$: previewUrl = selectedPrinter
		? getPreviewUrl(selectedPrinter.id, containerId, selectedTemplate)
		: '';

	$: previewKey = `${selectedPrinter?.id}-${containerId}-${selectedTemplate}`;

	onMount(async () => {
		await loadPrinters();
	});

	async function loadPrinters() {
		loading = true;
		error = '';
		try {
			printers = await getPrinters();
			// Select default printer or first available
			selectedPrinter = printers.find((p) => p.is_default) || printers[0] || null;
			if (selectedPrinter) {
				await detectPrinterMedia();
			}
		} catch (e) {
			error = 'Failed to load printers';
			console.error(e);
		} finally {
			loading = false;
		}
	}

	async function detectPrinterMedia() {
		if (!selectedPrinter) return;

		detectingMedia = true;
		try {
			mediaSuggestion = await detectMedia(selectedPrinter.id);
			if (mediaSuggestion.detected.supported && !mediaSuggestion.detected.error_message) {
				suggestedTemplate = mediaSuggestion.suggested_template;
				// Auto-select suggested template
				selectedTemplate = mediaSuggestion.suggested_template;
			}
		} catch (e) {
			console.error('Media detection failed:', e);
			// Non-critical, don't show error to user
		} finally {
			detectingMedia = false;
		}
	}

	async function handlePrinterChange() {
		mediaSuggestion = null;
		suggestedTemplate = null;
		if (selectedPrinter) {
			await detectPrinterMedia();
		}
	}

	async function handlePrint() {
		if (!selectedPrinter) return;

		// For PDF printers, trigger a download instead
		if (isPdfPrinter) {
			const downloadUrl = getDownloadUrl(selectedPrinter.id, containerId, selectedTemplate);
			// Create a temporary link and click it to trigger download
			const link = document.createElement('a');
			link.href = downloadUrl;
			link.download = '';
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			dispatch('printed', { success: true, message: 'PDF downloaded' });
			close();
			return;
		}

		printing = true;
		error = '';
		try {
			const result = await printLabel(selectedPrinter.id, containerId, selectedTemplate);
			if (result.success) {
				dispatch('printed', result);
				close();
			} else {
				error = result.message || 'Print failed';
			}
		} catch (e) {
			error = 'Print failed. Please try again.';
			console.error(e);
		} finally {
			printing = false;
		}
	}

	function close() {
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-40 bg-black/50"
		transition:fade={{ duration: 200 }}
		on:click={close}
		on:keypress={close}
		role="button"
		tabindex="-1"
	/>

	<!-- Modal -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4"
		transition:scale={{ duration: 200, start: 0.95 }}
	>
		<div
			class="w-full max-w-2xl rounded-xl bg-white dark:bg-slate-800 shadow-xl max-h-[90vh] overflow-y-auto"
			on:click|stopPropagation
			on:keypress|stopPropagation
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
		>
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 px-6 py-4">
				<h2 id="modal-title" class="text-lg font-semibold text-slate-900 dark:text-white">
					Print Label {containerName ? `- ${containerName}` : ''}
				</h2>
				<button
					type="button"
					class="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
					on:click={close}
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Body -->
			<div class="p-6 space-y-6">
				{#if loading}
					<div class="flex items-center justify-center py-8">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
					</div>
				{:else if printers.length === 0}
					<div class="text-center py-8">
						<svg
							class="mx-auto h-12 w-12 text-slate-400"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
							/>
						</svg>
						<h3 class="mt-2 text-sm font-medium text-slate-900 dark:text-white">No printers configured</h3>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Add a printer in Settings to start printing labels.
						</p>
					</div>
				{:else}
					<!-- Printer Selection -->
					<div>
						<label for="printer" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
							Printer
						</label>
						<select
							id="printer"
							bind:value={selectedPrinter}
							on:change={handlePrinterChange}
							class="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
						>
							{#each printers as printer}
								<option value={printer}>
									{printer.name}
									{printer.is_default ? '(Default)' : ''}
									- {printer.label_width_mm}x{printer.label_height_mm}mm
								</option>
							{/each}
						</select>
					</div>

					<!-- Media Detection Info -->
					{#if selectedPrinter}
						<MediaInfo suggestion={mediaSuggestion} loading={detectingMedia} printerType={selectedPrinter.printer_type} />
					{/if}

					<!-- Template Selection -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"> Label Template </label>
						<TemplateSelector
							bind:selected={selectedTemplate}
							{suggestedTemplate}
						/>
					</div>

					<!-- Preview -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"> Preview </label>
						<div class="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-slate-50 dark:bg-slate-900">
							{#key previewKey}
								{#if previewUrl}
									<img
										src={previewUrl}
										alt="Label preview"
										class="mx-auto max-h-48 object-contain"
									/>
								{:else}
									<div class="text-center text-slate-500 dark:text-slate-400 py-8">
										Select a printer to see preview
									</div>
								{/if}
							{/key}
						</div>
						{#if selectedPrinter}
							<p class="mt-2 text-xs text-slate-500 dark:text-slate-400 text-center">
								Actual size: {selectedPrinter.label_width_mm}mm x {selectedPrinter.label_height_mm}mm
							</p>
						{/if}
					</div>

					{#if error}
						<div class="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
							{error}
						</div>
					{/if}
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex justify-end gap-3 border-t border-slate-200 dark:border-slate-700 px-6 py-4">
				<button
					type="button"
					class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
					on:click={close}
				>
					Cancel
				</button>
				<button
					type="button"
					class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
					disabled={!selectedPrinter || printing || loading}
					on:click={handlePrint}
				>
					{#if printing}
						<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
						Printing...
					{:else if isPdfPrinter}
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
							/>
						</svg>
						Download PDF
					{:else}
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
							/>
						</svg>
						Print
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
