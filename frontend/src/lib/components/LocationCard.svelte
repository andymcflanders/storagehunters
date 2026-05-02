<script lang="ts">
	import type { Location } from '$lib/types';
	import Card from './ui/Card.svelte';
	import { _ } from '$lib/i18n';

	export let location: Location;
	export let containerCount = 0;
</script>

<a href="/locations/{location.id}" class="block">
	<Card hover>
		<div class="flex items-start justify-between">
			<div>
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">{location.name}</h3>
				{#if location.description}
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{location.description}</p>
				{/if}
			</div>

			<!-- Icon -->
			<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400">
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
					/>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
					/>
				</svg>
			</div>
		</div>

		{#if location.address}
			<p class="mt-3 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
					/>
				</svg>
				{location.address}
			</p>
		{/if}

		<div class="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-700 pt-4">
			<span class="text-sm text-slate-500 dark:text-slate-400">
				{$_('locations.containerCount', { values: { count: containerCount } })}
			</span>
			<svg class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
		</div>
	</Card>
</a>
