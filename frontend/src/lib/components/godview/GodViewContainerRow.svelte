<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { flip } from 'svelte/animate';
	import { dndzone, TRIGGERS, SHADOW_PLACEHOLDER_ITEM_ID } from 'svelte-dnd-action';
	import GodViewItemRow from './GodViewItemRow.svelte';
	import InlineEditField from './InlineEditField.svelte';
	import type { GodViewContainer, GodViewItem, GodViewUserInfo } from '$lib/types';

	export let container: GodViewContainer;
	export let users: GodViewUserInfo[];
	export let depth = 0;
	export let expanded = true;
	export let expandedItems: Set<string> = new Set();
	export let selectedForPrint: Set<string> = new Set();

	const dispatch = createEventDispatcher<{
		updateContainer: { id: string; field: string; value: string };
		deleteContainer: { id: string; name: string; itemCount: number; childCount: number };
		updateItem: { id: string; field: string; value: string | number | null };
		deleteItem: { id: string };
		toggleItemExpand: { id: string };
		toggleContainerExpand: { id: string };
		moveItem: { itemId: string; targetContainerId: string };
		printContainer: { id: string; name: string };
		togglePrintSelection: { id: string; name: string };
	}>();

	$: isSelectedForPrint = selectedForPrint.has(container.id);

	function handlePrintContainer() {
		dispatch('printContainer', { id: container.id, name: container.name });
	}

	function handleTogglePrintSelection() {
		dispatch('togglePrintSelection', { id: container.id, name: container.name });
	}

	// Local items for drag and drop
	let localItems: GodViewItem[] = [];
	$: localItems = [...container.items];

	const flipDurationMs = 200;

	function handleContainerFieldSave(field: string, value: string) {
		dispatch('updateContainer', { id: container.id, field, value });
	}

	function countAllItems(cont: GodViewContainer): number {
		let count = cont.items.length;
		for (const child of cont.children) {
			count += countAllItems(child);
		}
		return count;
	}

	function countAllChildren(cont: GodViewContainer): number {
		let count = cont.children.length;
		for (const child of cont.children) {
			count += countAllChildren(child);
		}
		return count;
	}

	function handleDeleteContainer() {
		// Count all items and children recursively
		const itemCount = countAllItems(container);
		const childCount = countAllChildren(container);
		dispatch('deleteContainer', {
			id: container.id,
			name: container.name,
			itemCount,
			childCount
		});
	}

	function toggleExpand() {
		dispatch('toggleContainerExpand', { id: container.id });
	}

	function handleItemUpdate(e: CustomEvent<{ id: string; field: string; value: string | number | null }>) {
		dispatch('updateItem', e.detail);
	}

	function handleItemDelete(e: CustomEvent<{ id: string }>) {
		dispatch('deleteItem', e.detail);
	}

	function handleItemToggleExpand(e: CustomEvent<{ id: string }>) {
		dispatch('toggleItemExpand', e.detail);
	}

	function handleNestedContainerUpdate(e: CustomEvent<{ id: string; field: string; value: string }>) {
		dispatch('updateContainer', e.detail);
	}

	function handleNestedContainerDelete(e: CustomEvent<{ id: string; name: string; itemCount: number; childCount: number }>) {
		dispatch('deleteContainer', e.detail);
	}

	function handleNestedMoveItem(e: CustomEvent<{ itemId: string; targetContainerId: string }>) {
		dispatch('moveItem', e.detail);
	}

	// Handle drag and drop
	function handleDndConsider(e: CustomEvent<{ items: GodViewItem[]; info: { trigger: string } }>) {
		localItems = e.detail.items;
	}

	function handleDndFinalize(e: CustomEvent<{ items: GodViewItem[]; info: { trigger: string; id: string } }>) {
		localItems = e.detail.items;

		// Check if an item was dropped here from another container
		const { trigger, id } = e.detail.info;
		if (trigger === TRIGGERS.DROPPED_INTO_ZONE && id !== SHADOW_PLACEHOLDER_ITEM_ID) {
			// Find if this item wasn't originally in this container
			const wasInContainer = container.items.some(item => item.id === id);
			if (!wasInContainer) {
				dispatch('moveItem', { itemId: id, targetContainerId: container.id });
			}
		}
	}

	$: paddingLeft = 16 + depth * 24;
	$: totalItems = container.items.length;
	$: totalChildren = container.children.length;
</script>

<!-- Container Header Row -->
<tr class="group border-b border-slate-200 bg-slate-50 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-750 {isSelectedForPrint ? 'ring-2 ring-inset ring-primary-400' : ''}">
	<!-- Checkbox + Expand -->
	<td class="w-16 px-2 py-2" style="padding-left: {paddingLeft}px">
		<div class="flex items-center gap-1">
			<!-- Checkbox for print selection -->
			<input
				type="checkbox"
				checked={isSelectedForPrint}
				on:change={handleTogglePrintSelection}
				class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400 focus:ring-primary-500 cursor-pointer"
				title="Select for batch printing"
			/>
			<!-- Expand button -->
			<button
				class="rounded p-0.5 text-slate-500 dark:text-slate-400 hover:bg-slate-200 hover:text-slate-700 dark:hover:bg-slate-600 dark:hover:text-slate-300"
				on:click={toggleExpand}
				title={expanded ? 'Collapse' : 'Expand'}
			>
				<svg class="h-4 w-4 transition-transform {expanded ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
		</div>
	</td>

	<!-- Container icon -->
	<td class="w-12 px-1 py-2">
		<div class="flex h-8 w-8 items-center justify-center rounded bg-primary-100 dark:bg-primary-900/30">
			<svg class="h-5 w-5 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
			</svg>
		</div>
	</td>

	<!-- Name -->
	<td class="min-w-[150px] max-w-[200px] px-1 py-2">
		<div class="flex items-center gap-2">
			<InlineEditField
				value={container.name}
				placeholder="Container name"
				className="font-semibold"
				on:save={(e) => handleContainerFieldSave('name', e.detail)}
			/>
			<span class="shrink-0 text-xs text-slate-400">
				{totalItems} item{totalItems !== 1 ? 's' : ''}{#if totalChildren > 0}, {totalChildren} nested{/if}
			</span>
		</div>
	</td>

	<!-- Notes (spans description column) -->
	<td class="min-w-[150px] max-w-[250px] px-1 py-2">
		<InlineEditField value={container.notes || ''} placeholder="Notes" on:save={(e) => handleContainerFieldSave('notes', e.detail)} />
	</td>

	<!-- QR Code -->
	<td class="w-20 px-1 py-2">
		<span class="font-mono text-xs text-slate-500 dark:text-slate-400">{container.qr_code}</span>
	</td>

	<!-- Empty cells for alignment -->
	<td class="w-28 px-1 py-2"></td>
	<td class="w-24 px-1 py-2"></td>
	<td class="w-28 px-1 py-2"></td>

	<!-- Actions -->
	<td class="w-16 px-2 py-2">
		<div class="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
			<!-- Print single label -->
			<button
				class="rounded p-1 text-slate-400 hover:bg-blue-100 hover:text-blue-600 dark:hover:bg-blue-900/30"
				on:click={handlePrintContainer}
				title="Print label for this container"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
				</svg>
			</button>
			<a
				href="/containers/{container.id}"
				class="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-primary-600 dark:hover:bg-slate-700"
				title="Open container page"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
				</svg>
			</a>
			<button
				class="rounded p-1 text-slate-400 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/30"
				on:click={handleDeleteContainer}
				title="Delete container"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
				</svg>
			</button>
		</div>
	</td>
</tr>

<!-- Expanded Content: Nested containers then items -->
{#if expanded}
	<!-- Nested containers -->
	{#each container.children as childContainer (childContainer.id)}
		<svelte:self
			container={childContainer}
			{users}
			depth={depth + 1}
			{expanded}
			{expandedItems}
			{selectedForPrint}
			on:updateContainer={handleNestedContainerUpdate}
			on:deleteContainer={handleNestedContainerDelete}
			on:updateItem={handleItemUpdate}
			on:deleteItem={handleItemDelete}
			on:toggleItemExpand={handleItemToggleExpand}
			on:toggleContainerExpand
			on:moveItem={handleNestedMoveItem}
			on:printContainer
			on:togglePrintSelection
		/>
	{/each}

	<!-- Items drop zone -->
	{#if localItems.length > 0 || expanded}
		<tr>
			<td colspan="9" class="p-0">
				<div
					class="min-h-[4px] transition-colors"
					use:dndzone={{
						items: localItems,
						flipDurationMs,
						dropTargetStyle: {},
						dropTargetClasses: ['bg-primary-100', 'dark:bg-primary-900/30'],
						type: 'item'
					}}
					on:consider={handleDndConsider}
					on:finalize={handleDndFinalize}
				>
					{#each localItems as item (item.id)}
						<div class="item-row" animate:flip={{ duration: flipDurationMs }}>
							<table class="w-full">
								<tbody>
									<GodViewItemRow
										{item}
										{users}
										depth={depth + 1}
										expanded={expandedItems.has(item.id)}
										draggable={true}
										on:update={handleItemUpdate}
										on:delete={handleItemDelete}
										on:toggleExpand={handleItemToggleExpand}
									/>
								</tbody>
							</table>
						</div>
					{/each}
				</div>
			</td>
		</tr>
	{/if}
{/if}

<style>
	.item-row :global(table) {
		table-layout: fixed;
	}
</style>
