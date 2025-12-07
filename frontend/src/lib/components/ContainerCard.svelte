<script lang="ts">
	import type { Container, ContainerSummary } from '$lib/types';
	import Card from './ui/Card.svelte';

	export let container: Container | ContainerSummary;
	export let showQR = false;

	$: itemCount = 'item_count' in container ? container.item_count : 0;
</script>

<a href="/containers/{container.id}" class="block">
	<Card hover>
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">{container.name}</h3>
				{#if 'notes' in container && container.notes}
					<p class="mt-1 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">{container.notes}</p>
				{/if}
			</div>

			<!-- QR Code Preview -->
			{#if showQR}
				<div class="ml-4 flex h-12 w-12 items-center justify-center rounded bg-slate-100 dark:bg-slate-700">
					<svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
						/>
					</svg>
				</div>
			{:else}
				<div
					class="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400"
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
						/>
					</svg>
				</div>
			{/if}
		</div>

		<div class="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-700 pt-4">
			<span class="text-sm text-slate-500 dark:text-slate-400">
				{itemCount}
				{itemCount === 1 ? 'item' : 'items'}
			</span>
			<svg class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
		</div>
	</Card>
</a>
