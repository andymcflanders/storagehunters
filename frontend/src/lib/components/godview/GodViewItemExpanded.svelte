<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import InlineEditField from './InlineEditField.svelte';
	import InlineEditSelect from './InlineEditSelect.svelte';
	import type { GodViewItem, GodViewUserInfo, Condition, Seasonal } from '$lib/types';
	import { _ } from '$lib/i18n';
	import { CONDITION_KEYS, SEASONAL_KEYS } from '$lib/utils/itemEnums';

	export let item: GodViewItem;
	export let users: GodViewUserInfo[];
	export let depth = 0;

	const dispatch = createEventDispatcher<{
		update: { id: string; field: string; value: string | number | null };
		close: void;
	}>();

	const CONDITION_COLORS: Record<Condition, string> = {
		good: 'text-green-600 dark:text-green-400',
		fair: 'text-yellow-600 dark:text-yellow-400',
		damaged: 'text-red-600 dark:text-red-400',
		needs_repair: 'text-orange-600 dark:text-orange-400'
	};
	const SEASONAL_COLORS: Record<Seasonal, string> = {
		none: 'text-slate-500',
		spring: 'text-green-600 dark:text-green-400',
		summer: 'text-yellow-600 dark:text-yellow-400',
		fall: 'text-orange-600 dark:text-orange-400',
		winter: 'text-blue-600 dark:text-blue-400',
		holiday: 'text-red-600 dark:text-red-400'
	};

	$: conditionOptions = (Object.keys(CONDITION_KEYS) as Condition[]).map((value) => ({
		value,
		label: $_(CONDITION_KEYS[value]),
		color: CONDITION_COLORS[value]
	}));
	$: seasonalOptions = (Object.keys(SEASONAL_KEYS) as Seasonal[]).map((value) => ({
		value,
		label: $_(SEASONAL_KEYS[value]),
		color: SEASONAL_COLORS[value]
	}));

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

	function handleValueChange(value: string) {
		const numValue = value ? parseFloat(value) : null;
		dispatch('update', { id: item.id, field: 'value_estimate', value: numValue });
	}

	function handleClose() {
		dispatch('close');
	}

	$: paddingLeft = 24 + depth * 24 + 40; // Extra indent for expanded view
</script>

<tr class="border-b border-slate-100 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-900/50">
	<td colspan="9" style="padding-left: {paddingLeft}px" class="py-4 pr-4">
		<div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
			<!-- Header -->
			<div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3 dark:border-slate-700">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Item Details: {item.name}</h3>
				<button
					class="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
					on:click={handleClose}
					title="Close expanded view"
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<div class="flex gap-6">
				<!-- Image Section -->
				<div class="shrink-0">
					{#if item.thumbnail_url}
						<a href="/items/{item.id}" class="block">
							<img
								src={item.thumbnail_url}
								alt={item.name}
								class="h-40 w-40 rounded-lg object-cover shadow-md transition-transform hover:scale-105"
							/>
						</a>
					{:else}
						<div class="flex h-40 w-40 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
							<svg class="h-16 w-16 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
					{/if}
					<p class="mt-2 text-center text-xs text-slate-500 dark:text-slate-400">
						{#if item.thumbnail_url}
							Click to view full page
						{:else}
							No image
						{/if}
					</p>
				</div>

				<!-- Details Grid -->
				<div class="flex-1 grid grid-cols-1 gap-x-8 gap-y-4 lg:grid-cols-3">

				<!-- Core Fields -->
				<div class="space-y-3">
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Name</label>
						<InlineEditField value={item.name} placeholder="Item name" on:save={(e) => handleFieldSave('name', e.detail)} />
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Description</label>
						<InlineEditField value={item.description || ''} placeholder="Description" on:save={(e) => handleFieldSave('description', e.detail)} />
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Size</label>
						<InlineEditField value={item.size || ''} placeholder="Size" on:save={(e) => handleFieldSave('size', e.detail)} />
					</div>
				</div>

				<div class="space-y-3">
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Condition</label>
						<InlineEditSelect value={item.condition} options={conditionOptions} on:change={(e) => handleSelectChange('condition', e.detail)} />
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Seasonal</label>
						<InlineEditSelect value={item.seasonal} options={seasonalOptions} on:change={(e) => handleSelectChange('seasonal', e.detail)} />
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Owner</label>
						<select
							value={item.owner_id || ''}
							on:change={handleOwnerChange}
							class="w-full cursor-pointer rounded border border-slate-200 bg-white px-2 py-1 text-sm outline-none hover:border-primary-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:hover:border-primary-500 dark:focus:ring-primary-800"
						>
							<option value="">Unassigned</option>
							{#each users as user}
								<option value={user.id}>{user.name}</option>
							{/each}
						</select>
					</div>
				</div>

				<!-- Value and AI Fields -->
				<div class="space-y-3">
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Estimated Value</label>
						<InlineEditField
							value={item.value_estimate?.toString() || ''}
							placeholder="0.00"
							on:save={(e) => handleValueChange(e.detail)}
						/>
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Needs Review</label>
						<span class="inline-flex items-center rounded-full px-2 py-1 text-xs font-medium {item.needs_review ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'}">
							{item.needs_review ? 'Yes' : 'No'}
						</span>
					</div>
				</div>

				<!-- AI Generated Content -->
				{#if item.ai_processed}
					<div class="col-span-2 space-y-3 rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20 lg:col-span-3">
						<h4 class="flex items-center gap-2 text-sm font-semibold text-blue-800 dark:text-blue-300">
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
							</svg>
							AI Generated Content
						</h4>
						<div class="grid grid-cols-2 gap-4">
							{#each Object.entries(item.ai_names || {}) as [code, value]}
								<div>
									<label class="mb-1 block text-xs font-medium text-blue-700 dark:text-blue-400">AI Name ({code.toUpperCase()})</label>
									<p class="text-sm text-blue-900 dark:text-blue-200">{value || '-'}</p>
								</div>
							{/each}
							{#each Object.entries(item.ai_descriptions || {}) as [code, value]}
								<div>
									<label class="mb-1 block text-xs font-medium text-blue-700 dark:text-blue-400">AI Description ({code.toUpperCase()})</label>
									<p class="text-sm text-blue-900 dark:text-blue-200">{value || '-'}</p>
								</div>
							{/each}
							{#if Object.keys(item.ai_names || {}).length === 0 && Object.keys(item.ai_descriptions || {}).length === 0}
								<p class="col-span-2 text-sm text-blue-900 dark:text-blue-200">No AI content yet</p>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Timestamps -->
				<div class="col-span-1 flex gap-6 border-t border-slate-200 pt-3 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400 lg:col-span-3">
					<span>Created: {new Date(item.created_at).toLocaleString()}</span>
					<span>Updated: {new Date(item.updated_at).toLocaleString()}</span>
				</div>
				</div><!-- End Details Grid -->
			</div><!-- End Flex Container -->

			<!-- Actions -->
			<div class="mt-4 flex justify-end gap-2 border-t border-slate-200 pt-4 dark:border-slate-700">
				<a
					href="/items/{item.id}"
					class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
				>
					Open Full Item Page
				</a>
			</div>
		</div>
	</td>
</tr>
