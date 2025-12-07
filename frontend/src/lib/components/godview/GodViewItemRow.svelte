<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import InlineEditField from './InlineEditField.svelte';
	import InlineEditSelect from './InlineEditSelect.svelte';
	import GodViewItemExpanded from './GodViewItemExpanded.svelte';
	import type { GodViewItem, GodViewUserInfo, Condition, Seasonal } from '$lib/types';

	export let item: GodViewItem;
	export let users: GodViewUserInfo[];
	export let depth = 0;
	export let expanded = false;
	export let draggable = false;

	const dispatch = createEventDispatcher<{
		update: { id: string; field: string; value: string | number | null };
		delete: { id: string };
		toggleExpand: { id: string };
	}>();

	const conditionOptions: { value: Condition; label: string; color: string }[] = [
		{ value: 'good', label: 'Good', color: 'text-green-600 dark:text-green-400' },
		{ value: 'fair', label: 'Fair', color: 'text-yellow-600 dark:text-yellow-400' },
		{ value: 'damaged', label: 'Damaged', color: 'text-red-600 dark:text-red-400' },
		{ value: 'needs_repair', label: 'Needs Repair', color: 'text-orange-600 dark:text-orange-400' }
	];

	const seasonalOptions: { value: Seasonal; label: string; color: string }[] = [
		{ value: 'none', label: 'None', color: 'text-slate-500' },
		{ value: 'spring', label: 'Spring', color: 'text-green-600 dark:text-green-400' },
		{ value: 'summer', label: 'Summer', color: 'text-yellow-600 dark:text-yellow-400' },
		{ value: 'fall', label: 'Fall', color: 'text-orange-600 dark:text-orange-400' },
		{ value: 'winter', label: 'Winter', color: 'text-blue-600 dark:text-blue-400' },
		{ value: 'holiday', label: 'Holiday', color: 'text-red-600 dark:text-red-400' }
	];

	function handleFieldSave(field: string, value: string) {
		dispatch('update', { id: item.id, field, value });
	}

	function handleSelectChange(field: string, value: string) {
		dispatch('update', { id: item.id, field, value });
	}

	function handleOwnerChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const value = target.value || null;
		dispatch('update', { id: item.id, field: 'owner_id', value });
	}

	function handleDelete() {
		if (confirm(`Delete "${item.name}"?`)) {
			dispatch('delete', { id: item.id });
		}
	}

	function toggleExpand() {
		dispatch('toggleExpand', { id: item.id });
	}

	$: paddingLeft = 24 + depth * 24;
</script>

<tr class="group border-b border-slate-100 bg-white hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-850">
	<!-- Drag handle + Expand -->
	<td class="w-16 px-2 py-1" style="padding-left: {paddingLeft}px">
		<div class="flex items-center gap-1">
			<!-- Drag handle -->
			{#if draggable}
				<div class="cursor-grab text-slate-300 opacity-0 transition-opacity group-hover:opacity-100 active:cursor-grabbing dark:text-slate-600">
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
						<circle cx="9" cy="5" r="1.5" />
						<circle cx="15" cy="5" r="1.5" />
						<circle cx="9" cy="12" r="1.5" />
						<circle cx="15" cy="12" r="1.5" />
						<circle cx="9" cy="19" r="1.5" />
						<circle cx="15" cy="19" r="1.5" />
					</svg>
				</div>
			{/if}
			<!-- Expand button -->
			<button
				class="rounded p-0.5 text-slate-400 hover:bg-slate-200 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
				on:click={toggleExpand}
				title={expanded ? 'Collapse' : 'Expand details'}
			>
				<svg class="h-4 w-4 transition-transform {expanded ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
		</div>
	</td>

	<!-- Thumbnail -->
	<td class="w-12 px-1 py-1">
		{#if item.thumbnail_url}
			<img src={item.thumbnail_url} alt="" class="h-8 w-8 rounded object-cover" />
		{:else}
			<div class="flex h-8 w-8 items-center justify-center rounded bg-slate-100 dark:bg-slate-800">
				<svg class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
			</div>
		{/if}
	</td>

	<!-- Name -->
	<td class="min-w-[150px] max-w-[200px] px-1 py-1">
		<InlineEditField value={item.name} placeholder="Item name" on:save={(e) => handleFieldSave('name', e.detail)} />
	</td>

	<!-- Description -->
	<td class="min-w-[150px] max-w-[250px] px-1 py-1">
		<InlineEditField value={item.description || ''} placeholder="Description" on:save={(e) => handleFieldSave('description', e.detail)} />
	</td>

	<!-- Size -->
	<td class="w-20 px-1 py-1">
		<InlineEditField value={item.size || ''} placeholder="Size" on:save={(e) => handleFieldSave('size', e.detail)} />
	</td>

	<!-- Condition -->
	<td class="w-28 px-1 py-1">
		<InlineEditSelect value={item.condition} options={conditionOptions} on:change={(e) => handleSelectChange('condition', e.detail)} />
	</td>

	<!-- Seasonal -->
	<td class="w-24 px-1 py-1">
		<InlineEditSelect value={item.seasonal} options={seasonalOptions} on:change={(e) => handleSelectChange('seasonal', e.detail)} />
	</td>

	<!-- Owner -->
	<td class="w-28 px-1 py-1">
		<select
			value={item.owner_id || ''}
			on:change={handleOwnerChange}
			class="cursor-pointer rounded border-0 bg-transparent px-1 py-0.5 text-sm outline-none hover:bg-slate-100 focus:ring-2 focus:ring-primary-200 dark:hover:bg-slate-700 dark:focus:ring-primary-800"
		>
			<option value="">Unassigned</option>
			{#each users as user}
				<option value={user.id}>{user.name}</option>
			{/each}
		</select>
	</td>

	<!-- Actions -->
	<td class="w-16 px-2 py-1">
		<div class="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
			<a
				href="/items/{item.id}"
				class="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-primary-600 dark:hover:bg-slate-700"
				title="Open item page"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
				</svg>
			</a>
			<button
				class="rounded p-1 text-slate-400 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/30"
				on:click={handleDelete}
				title="Delete item"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
				</svg>
			</button>
		</div>
	</td>
</tr>

<!-- Expanded Item Details -->
{#if expanded}
	<GodViewItemExpanded
		{item}
		{users}
		{depth}
		on:update
		on:close={() => dispatch('toggleExpand', { id: item.id })}
	/>
{/if}
