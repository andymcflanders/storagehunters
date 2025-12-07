<script lang="ts">
	import type { Item, ItemSummary } from '$lib/types';
	import Card from './ui/Card.svelte';

	export let item: Item | ItemSummary;

	$: thumbnailUrl = 'thumbnail_url' in item ? item.thumbnail_url : null;
</script>

<a href="/items/{item.id}" class="block">
	<Card hover padding="none">
		<!-- Thumbnail -->
		<div class="aspect-square w-full overflow-hidden rounded-t-xl bg-slate-100 dark:bg-slate-700">
			{#if thumbnailUrl}
				<img src={thumbnailUrl} alt={item.name} class="h-full w-full object-cover" />
			{:else}
				<div class="flex h-full w-full items-center justify-center">
					<svg class="h-12 w-12 text-slate-300 dark:text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
						/>
					</svg>
				</div>
			{/if}
		</div>

		<!-- Content -->
		<div class="p-4">
			<h3 class="font-medium text-slate-900 dark:text-white line-clamp-1">{item.name}</h3>

			{#if 'condition' in item}
				<div class="mt-2 flex items-center gap-2">
					<span
						class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
						{item.condition === 'good'
							? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
							: item.condition === 'fair'
								? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
								: item.condition === 'damaged'
									? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
									: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'}"
					>
						{item.condition.replace('_', ' ')}
					</span>

					{#if item.seasonal !== 'none'}
						<span class="inline-flex items-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 px-2 py-0.5 text-xs font-medium">
							{item.seasonal}
						</span>
					{/if}
				</div>
			{/if}
		</div>
	</Card>
</a>
