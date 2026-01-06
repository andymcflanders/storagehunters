<script lang="ts">
	import type { MediaSuggestion, PrinterType } from '$lib/types';

	export let suggestion: MediaSuggestion | null = null;
	export let loading = false;
	export let printerType: PrinterType | null = null;

	// PDF and network printers don't support media detection - that's expected
	$: isNonDetectingPrinter = printerType === 'generic_pdf' || printerType === 'network_ipp';
</script>

<div class="bg-slate-50 dark:bg-slate-900 rounded-lg p-3 text-sm">
	{#if loading}
		<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
			<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-400"></div>
			Detecting media...
		</div>
	{:else if suggestion}
		{#if suggestion.detected.supported && !suggestion.detected.error_message}
			<div class="flex items-start gap-3">
				<!-- Status indicator -->
				<div
					class="flex-shrink-0 mt-0.5 w-2 h-2 rounded-full {suggestion.detected.printer_status ===
					'ready'
						? 'bg-green-500'
						: suggestion.detected.printer_status === 'out_of_media'
							? 'bg-red-500'
							: 'bg-yellow-500'}"
				></div>

				<div class="flex-1">
					<!-- Detected dimensions -->
					<div class="flex items-center gap-2 flex-wrap">
						<span class="font-medium text-slate-700 dark:text-slate-300">Detected:</span>
						{#if suggestion.detected.width_mm}
							<span class="text-slate-600 dark:text-slate-400">
								{suggestion.detected.width_mm.toFixed(1)}mm
								{#if suggestion.detected.height_mm}
									x {suggestion.detected.height_mm.toFixed(1)}mm
								{:else}
									(continuous)
								{/if}
							</span>
						{:else}
							<span class="text-slate-500 dark:text-slate-400 italic">Unknown dimensions</span>
						{/if}

						{#if suggestion.detected.media_type !== 'unknown'}
							<span
								class="px-2 py-0.5 rounded text-xs {suggestion.detected.media_type === 'die_cut'
									? 'bg-blue-100 text-blue-700'
									: 'bg-purple-100 text-purple-700'}"
							>
								{suggestion.detected.media_type === 'die_cut' ? 'Die-cut' : 'Continuous'}
							</span>
						{/if}
					</div>

					<!-- Suggestion reason -->
					{#if suggestion.reason}
						<p class="mt-1 text-slate-500 dark:text-slate-400 text-xs">
							{suggestion.reason}
						</p>
					{/if}

					<!-- Confidence indicator -->
					{#if suggestion.confidence}
						<div class="mt-1 flex items-center gap-1">
							<span class="text-xs text-slate-400 dark:text-slate-500">Confidence:</span>
							<div class="flex gap-0.5">
								<div
									class="w-2 h-2 rounded-full {suggestion.confidence === 'low'
										? 'bg-slate-300'
										: 'bg-green-400'}"
								></div>
								<div
									class="w-2 h-2 rounded-full {suggestion.confidence === 'high' ||
									suggestion.confidence === 'medium'
										? 'bg-green-400'
										: 'bg-slate-300'}"
								></div>
								<div
									class="w-2 h-2 rounded-full {suggestion.confidence === 'high'
										? 'bg-green-400'
										: 'bg-slate-300'}"
								></div>
							</div>
						</div>
					{/if}
				</div>
			</div>
		{:else if suggestion.detected.error_message}
			{#if isNonDetectingPrinter}
				<!-- Friendly message for PDF/Network printers -->
				<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
					<svg class="h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<span>Select a template below based on your paper size</span>
				</div>
			{:else}
				<div class="flex items-center gap-2 text-amber-600 dark:text-amber-500">
					<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						/>
					</svg>
					<span>{suggestion.detected.error_message}</span>
				</div>
			{/if}
		{:else}
			{#if isNonDetectingPrinter}
				<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
					<svg class="h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					<span>Select a template below based on your paper size</span>
				</div>
			{:else}
				<div class="text-slate-500 dark:text-slate-400">
					Media detection not supported for this printer type
				</div>
			{/if}
		{/if}
	{:else}
		<div class="text-slate-500 dark:text-slate-400">Select a printer to detect media</div>
	{/if}
</div>
