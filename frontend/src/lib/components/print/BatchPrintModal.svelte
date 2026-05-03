<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import type { Printer, LabelTemplate, MediaSuggestion, BatchPrintResult } from '$lib/types';
	import { getPrinters, detectMedia, printBatch } from '$lib/api/printers';
	import TemplateSelector from './TemplateSelector.svelte';
	import MediaInfo from './MediaInfo.svelte';

	export let open = false;
	export let containerIds: string[] = [];
	export let containerNames: string[] = [];

	const dispatch = createEventDispatcher<{
		close: void;
		printed: BatchPrintResult;
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
	let result: BatchPrintResult | null = null;

	onMount(async () => {
		await loadPrinters();
	});

	async function loadPrinters() {
		loading = true;
		error = '';
		try {
			printers = await getPrinters();
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
				selectedTemplate = mediaSuggestion.suggested_template;
			}
		} catch (e) {
			console.error('Media detection failed:', e);
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
		if (!selectedPrinter || containerIds.length === 0) return;

		printing = true;
		error = '';
		result = null;
		try {
			result = await printBatch(selectedPrinter.id, containerIds, selectedTemplate);
			dispatch('printed', result);
		} catch (e) {
			error = 'Batch print failed. Please try again.';
			console.error(e);
		} finally {
			printing = false;
		}
	}

	function close() {
		result = null;
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
					Print {containerIds.length} Labels
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
				{#if result}
					<!-- Results view -->
					<div class="space-y-4">
						<div class="flex items-center gap-4">
							<div
								class="h-16 w-16 rounded-full flex items-center justify-center {result.failed === 0
									? 'bg-green-100'
									: result.success === 0
										? 'bg-red-100'
										: 'bg-amber-100'}"
							>
								{#if result.failed === 0}
									<svg class="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
									</svg>
								{:else if result.success === 0}
									<svg class="h-8 w-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
									</svg>
								{:else}
									<svg class="h-8 w-8 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
									</svg>
								{/if}
							</div>
							<div>
								<h3 class="text-lg font-semibold text-slate-900 dark:text-white">
									{#if result.failed === 0}
										All labels printed successfully!
									{:else if result.success === 0}
										Print failed
									{:else}
										Partially completed
									{/if}
								</h3>
								<p class="text-slate-500 dark:text-slate-400">
									{result.success} of {result.total} labels printed
								</p>
							</div>
						</div>

						{#if result.results.length > 0 && result.failed > 0}
							<div class="border border-slate-200 dark:border-slate-700 rounded-lg max-h-48 overflow-y-auto">
								{#each result.results as item}
									<div class="flex items-center gap-3 px-4 py-2 border-b border-slate-100 dark:border-slate-700 last:border-b-0">
										{#if item.success}
											<svg class="h-4 w-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
											</svg>
										{:else}
											<svg class="h-4 w-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
										{/if}
										<span class="flex-1 text-sm {item.success ? 'text-slate-700 dark:text-slate-300' : 'text-red-700 dark:text-red-400'}">
											{item.container_name || item.container_id}
										</span>
										{#if !item.success}
											<span class="text-xs text-red-500 dark:text-red-400">{item.message}</span>
										{/if}
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{:else if loading}
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
					<!-- Containers to print -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
							Containers ({containerIds.length})
						</label>
						<div class="border border-slate-200 dark:border-slate-700 rounded-lg p-3 bg-slate-50 dark:bg-slate-900 max-h-32 overflow-y-auto">
							<div class="flex flex-wrap gap-2">
								{#each containerNames as name, i}
									<span class="px-2 py-1 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded text-sm text-slate-700 dark:text-slate-300">
										{name}
									</span>
								{/each}
							</div>
						</div>
					</div>

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
						<TemplateSelector bind:selected={selectedTemplate} {suggestedTemplate} />
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
				{#if result}
					<button
						type="button"
						class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
						on:click={close}
					>
						Done
					</button>
				{:else}
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
						disabled={!selectedPrinter || printing || loading || containerIds.length === 0}
						on:click={handlePrint}
					>
						{#if printing}
							<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
							Printing {containerIds.length} labels...
						{:else}
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
								/>
							</svg>
							Print {containerIds.length} Labels
						{/if}
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}
