<script lang="ts">
	import type { PathElement } from '$lib/types';

	export let path: PathElement[] = [];
	export let currentName = '';
</script>

<nav class="flex items-center gap-2 text-sm">
	<a href="/" class="text-slate-500 dark:text-slate-400 hover:text-slate-700">
		<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
			/>
		</svg>
	</a>

	{#each path as element}
		<svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
		<a
			href="/{element.type === 'location' ? 'locations' : 'containers'}/{element.id}"
			class="text-slate-500 dark:text-slate-400 hover:text-slate-700"
		>
			{element.name}
		</a>
	{/each}

	{#if currentName}
		<svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
		<span class="font-medium text-slate-900 dark:text-white">{currentName}</span>
	{/if}
</nav>
