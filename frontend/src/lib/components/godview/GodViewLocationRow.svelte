<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import GodViewContainerRow from './GodViewContainerRow.svelte';
	import InlineEditField from './InlineEditField.svelte';
	import type { GodViewLocation, GodViewUserInfo } from '$lib/types';

	export let location: GodViewLocation;
	export let users: GodViewUserInfo[];
	export let expanded = true;
	export let expandedContainers: Set<string> = new Set();
	export let expandedItems: Set<string> = new Set();

	const dispatch = createEventDispatcher<{
		updateLocation: { id: string; field: string; value: string };
		deleteLocation: { id: string };
		updateContainer: { id: string; field: string; value: string };
		deleteContainer: { id: string; name: string; itemCount: number; childCount: number };
		createContainer: { locationId: string };
		updateItem: { id: string; field: string; value: string | number | null };
		deleteItem: { id: string };
		toggleItemExpand: { id: string };
		toggleContainerExpand: { id: string };
		toggleLocationExpand: { id: string };
		moveItem: { itemId: string; targetContainerId: string };
	}>();

	function handleCreateContainer() {
		dispatch('createContainer', { locationId: location.id });
	}

	function handleFieldSave(field: string, value: string) {
		dispatch('updateLocation', { id: location.id, field, value });
	}

	function handleDeleteLocation() {
		const containerCount = location.containers.length;
		let message = `Delete "${location.name}"?`;
		if (containerCount > 0) {
			message += `\n\nThis location has ${containerCount} container(s).`;
		}
		if (confirm(message)) {
			dispatch('deleteLocation', { id: location.id });
		}
	}

	function toggleExpand() {
		dispatch('toggleLocationExpand', { id: location.id });
	}

	// Count total items across all containers (including nested)
	function countItems(containers: typeof location.containers): number {
		let count = 0;
		for (const container of containers) {
			count += container.items.length;
			count += countItems(container.children);
		}
		return count;
	}

	$: totalContainers = location.containers.length;
	$: totalItems = countItems(location.containers);
</script>

<!-- Location Header Row -->
<tr class="group border-b-2 border-primary-200 bg-primary-50 hover:bg-primary-100 dark:border-primary-800 dark:bg-primary-950 dark:hover:bg-primary-900/50">
	<!-- Expand -->
	<td class="w-16 px-2 py-3">
		<div class="flex items-center gap-1">
			<!-- Expand button -->
			<button
				class="rounded p-1 text-primary-600 hover:bg-primary-200 dark:text-primary-400 dark:hover:bg-primary-800"
				on:click={toggleExpand}
				title={expanded ? 'Collapse' : 'Expand'}
			>
				<svg class="h-5 w-5 transition-transform {expanded ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
		</div>
	</td>

	<!-- Location icon -->
	<td class="w-12 px-1 py-3">
		<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-200 dark:bg-primary-800">
			<svg class="h-6 w-6 text-primary-700 dark:text-primary-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
			</svg>
		</div>
	</td>

	<!-- Name -->
	<td class="min-w-[150px] max-w-[200px] px-1 py-3">
		<div class="flex items-center gap-2">
			<InlineEditField
				value={location.name}
				placeholder="Location name"
				className="text-lg font-bold text-primary-900 dark:text-primary-100"
				on:save={(e) => handleFieldSave('name', e.detail)}
			/>
			<span class="shrink-0 text-sm text-primary-600 dark:text-primary-400">
				{totalContainers} container{totalContainers !== 1 ? 's' : ''}, {totalItems} item{totalItems !== 1 ? 's' : ''}
			</span>
		</div>
	</td>

	<!-- Empty cells for alignment -->
	<td class="min-w-[150px] max-w-[250px] px-1 py-3"></td>
	<td class="w-20 px-1 py-3"></td>
	<td class="w-28 px-1 py-3"></td>
	<td class="w-24 px-1 py-3"></td>
	<td class="w-28 px-1 py-3"></td>

	<!-- Actions -->
	<td class="w-24 px-2 py-3">
		<div class="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
			<button
				class="rounded p-1 text-primary-500 hover:bg-green-100 hover:text-green-600 dark:hover:bg-green-900/30"
				on:click={handleCreateContainer}
				title="Add container to this location"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
				</svg>
			</button>
			<a
				href="/locations/{location.id}"
				class="rounded p-1 text-primary-500 hover:bg-primary-200 hover:text-primary-700 dark:hover:bg-primary-800"
				title="Open location page"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
				</svg>
			</a>
			<button
				class="rounded p-1 text-primary-500 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/30"
				on:click={handleDeleteLocation}
				title="Delete location"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
				</svg>
			</button>
		</div>
	</td>
</tr>

<!-- Expanded Content: Containers -->
{#if expanded}
	{#each location.containers as container (container.id)}
		<GodViewContainerRow
			{container}
			{users}
			depth={0}
			expanded={expandedContainers.has(container.id) || expandedContainers.size === 0}
			{expandedItems}
			on:updateContainer
			on:deleteContainer
			on:updateItem
			on:deleteItem
			on:toggleItemExpand
			on:toggleContainerExpand
			on:moveItem
		/>
	{/each}
{/if}
