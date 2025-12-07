<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { GodViewUserInfo, GodViewLocation, Condition, Seasonal } from '$lib/types';

	export let users: GodViewUserInfo[] = [];
	export let locations: GodViewLocation[] = [];
	export let totalLocations = 0;
	export let totalContainers = 0;
	export let totalItems = 0;

	// Filter state
	export let searchQuery = '';
	export let filterCondition: Condition | '' = '';
	export let filterSeasonal: Seasonal | '' = '';
	export let filterOwner = '';
	export let filterNeedsReview: boolean | null = null;
	export let filterLocationIds: Set<string> = new Set();
	export let filterContainerIds: Set<string> = new Set();

	// Expand/collapse state
	export let allLocationsExpanded = true;
	export let allContainersExpanded = true;

	// Dropdown state
	let showLocationDropdown = false;
	let showContainerDropdown = false;

	const dispatch = createEventDispatcher<{
		search: string;
		filterCondition: Condition | '';
		filterSeasonal: Seasonal | '';
		filterOwner: string;
		filterNeedsReview: boolean | null;
		filterLocationIds: Set<string>;
		filterContainerIds: Set<string>;
		expandAllLocations: void;
		collapseAllLocations: void;
		expandAllContainers: void;
		collapseAllContainers: void;
		refresh: void;
	}>();

	const conditionOptions: { value: Condition | ''; label: string }[] = [
		{ value: '', label: 'All Conditions' },
		{ value: 'good', label: 'Good' },
		{ value: 'fair', label: 'Fair' },
		{ value: 'damaged', label: 'Damaged' },
		{ value: 'needs_repair', label: 'Needs Repair' }
	];

	const seasonalOptions: { value: Seasonal | ''; label: string }[] = [
		{ value: '', label: 'All Seasons' },
		{ value: 'none', label: 'None' },
		{ value: 'spring', label: 'Spring' },
		{ value: 'summer', label: 'Summer' },
		{ value: 'fall', label: 'Fall' },
		{ value: 'winter', label: 'Winter' },
		{ value: 'holiday', label: 'Holiday' }
	];

	// Build flat list of all containers with their location context
	interface ContainerOption {
		id: string;
		name: string;
		locationName: string;
		depth: number;
	}

	function flattenContainers(containers: GodViewLocation['containers'], locationName: string, depth = 0): ContainerOption[] {
		let result: ContainerOption[] = [];
		for (const container of containers) {
			result.push({ id: container.id, name: container.name, locationName, depth });
			result = result.concat(flattenContainers(container.children, locationName, depth + 1));
		}
		return result;
	}

	$: allContainers = locations.flatMap((loc) => flattenContainers(loc.containers, loc.name));

	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		dispatch('search', target.value);
	}

	function handleConditionChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		dispatch('filterCondition', target.value as Condition | '');
	}

	function handleSeasonalChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		dispatch('filterSeasonal', target.value as Seasonal | '');
	}

	function handleOwnerChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		dispatch('filterOwner', target.value);
	}

	function handleNeedsReviewChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const value = target.value;
		if (value === '') {
			dispatch('filterNeedsReview', null);
		} else {
			dispatch('filterNeedsReview', value === 'true');
		}
	}

	function toggleLocation(locationId: string) {
		const newSet = new Set(filterLocationIds);
		if (newSet.has(locationId)) {
			newSet.delete(locationId);
		} else {
			newSet.add(locationId);
		}
		dispatch('filterLocationIds', newSet);
	}

	function toggleContainer(containerId: string) {
		const newSet = new Set(filterContainerIds);
		if (newSet.has(containerId)) {
			newSet.delete(containerId);
		} else {
			newSet.add(containerId);
		}
		dispatch('filterContainerIds', newSet);
	}

	function clearLocationFilter() {
		dispatch('filterLocationIds', new Set());
	}

	function clearContainerFilter() {
		dispatch('filterContainerIds', new Set());
	}

	function toggleAllLocations() {
		if (allLocationsExpanded) {
			dispatch('collapseAllLocations');
		} else {
			dispatch('expandAllLocations');
		}
	}

	function toggleAllContainers() {
		if (allContainersExpanded) {
			dispatch('collapseAllContainers');
		} else {
			dispatch('expandAllContainers');
		}
	}

	function clearAllFilters() {
		dispatch('search', '');
		dispatch('filterCondition', '');
		dispatch('filterSeasonal', '');
		dispatch('filterOwner', '');
		dispatch('filterNeedsReview', null);
		dispatch('filterLocationIds', new Set());
		dispatch('filterContainerIds', new Set());
	}

	$: hasActiveFilters = searchQuery || filterCondition || filterSeasonal || filterOwner || filterNeedsReview !== null || filterLocationIds.size > 0 || filterContainerIds.size > 0;

	// Close dropdowns when clicking outside
	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.location-dropdown')) {
			showLocationDropdown = false;
		}
		if (!target.closest('.container-dropdown')) {
			showContainerDropdown = false;
		}
	}
</script>

<svelte:window on:click={handleClickOutside} />

<div class="mb-4 space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
	<!-- Top row: Search and stats -->
	<div class="flex flex-wrap items-center justify-between gap-4">
		<div class="flex items-center gap-4">
			<!-- Search -->
			<div class="relative">
				<svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					value={searchQuery}
					on:input={handleSearch}
					placeholder="Search items..."
					class="w-64 rounded-lg border border-slate-200 bg-white py-2 pl-10 pr-4 text-sm outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-primary-500 dark:focus:ring-primary-800"
				/>
			</div>

			<!-- Stats -->
			<div class="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
				<span class="rounded-full bg-primary-100 px-2 py-0.5 font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
					{totalLocations} locations
				</span>
				<span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-700 dark:bg-slate-700 dark:text-slate-300">
					{totalContainers} containers
				</span>
				<span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-700 dark:bg-slate-700 dark:text-slate-300">
					{totalItems} items
				</span>
			</div>
		</div>

		<!-- Actions -->
		<div class="flex items-center gap-2">
			<button
				class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
				on:click={toggleAllLocations}
				title={allLocationsExpanded ? 'Collapse all locations' : 'Expand all locations'}
			>
				<svg class="h-4 w-4 {allLocationsExpanded ? '' : 'rotate-180'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
				Locations
			</button>
			<button
				class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
				on:click={toggleAllContainers}
				title={allContainersExpanded ? 'Collapse all containers' : 'Expand all containers'}
			>
				<svg class="h-4 w-4 {allContainersExpanded ? '' : 'rotate-180'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
				Containers
			</button>
			<button
				class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
				on:click={() => dispatch('refresh')}
				title="Refresh data"
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				Refresh
			</button>
		</div>
	</div>

	<!-- Bottom row: Filters -->
	<div class="flex flex-wrap items-center gap-3">
		<span class="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Filters:</span>

		<!-- Location multi-select dropdown -->
		<div class="location-dropdown relative">
			<button
				class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm outline-none
					{filterLocationIds.size > 0
					? 'border-primary-400 bg-primary-50 text-primary-700 dark:border-primary-600 dark:bg-primary-900/30 dark:text-primary-300'
					: 'border-slate-200 bg-white text-slate-700 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300'}
					hover:bg-slate-50 dark:hover:bg-slate-600"
				on:click|stopPropagation={() => (showLocationDropdown = !showLocationDropdown)}
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				{filterLocationIds.size > 0 ? `${filterLocationIds.size} Location${filterLocationIds.size > 1 ? 's' : ''}` : 'All Locations'}
				<svg class="h-4 w-4 transition-transform {showLocationDropdown ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if showLocationDropdown}
				<div class="absolute left-0 top-full z-50 mt-1 max-h-64 min-w-[200px] overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-600 dark:bg-slate-800">
					{#if filterLocationIds.size > 0}
						<button
							class="w-full border-b border-slate-200 px-3 py-2 text-left text-sm text-primary-600 hover:bg-slate-50 dark:border-slate-700 dark:text-primary-400 dark:hover:bg-slate-700"
							on:click|stopPropagation={clearLocationFilter}
						>
							Clear selection
						</button>
					{/if}
					{#each locations as location}
						<label
							class="flex cursor-pointer items-center gap-2 px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700"
							on:click|stopPropagation
						>
							<input
								type="checkbox"
								checked={filterLocationIds.has(location.id)}
								on:change={() => toggleLocation(location.id)}
								class="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
							/>
							<span class="text-sm text-slate-700 dark:text-slate-300">{location.name}</span>
							<span class="ml-auto text-xs text-slate-400">{location.item_count} items</span>
						</label>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Container multi-select dropdown -->
		<div class="container-dropdown relative">
			<button
				class="flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm outline-none
					{filterContainerIds.size > 0
					? 'border-primary-400 bg-primary-50 text-primary-700 dark:border-primary-600 dark:bg-primary-900/30 dark:text-primary-300'
					: 'border-slate-200 bg-white text-slate-700 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300'}
					hover:bg-slate-50 dark:hover:bg-slate-600"
				on:click|stopPropagation={() => (showContainerDropdown = !showContainerDropdown)}
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
				</svg>
				{filterContainerIds.size > 0 ? `${filterContainerIds.size} Container${filterContainerIds.size > 1 ? 's' : ''}` : 'All Containers'}
				<svg class="h-4 w-4 transition-transform {showContainerDropdown ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if showContainerDropdown}
				<div class="absolute left-0 top-full z-50 mt-1 max-h-64 min-w-[280px] overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-600 dark:bg-slate-800">
					{#if filterContainerIds.size > 0}
						<button
							class="w-full border-b border-slate-200 px-3 py-2 text-left text-sm text-primary-600 hover:bg-slate-50 dark:border-slate-700 dark:text-primary-400 dark:hover:bg-slate-700"
							on:click|stopPropagation={clearContainerFilter}
						>
							Clear selection
						</button>
					{/if}
					{#each allContainers as container}
						<label
							class="flex cursor-pointer items-center gap-2 px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700"
							style="padding-left: {12 + container.depth * 16}px"
							on:click|stopPropagation
						>
							<input
								type="checkbox"
								checked={filterContainerIds.has(container.id)}
								on:change={() => toggleContainer(container.id)}
								class="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
							/>
							<span class="text-sm text-slate-700 dark:text-slate-300">{container.name}</span>
							<span class="ml-auto text-xs text-slate-400">{container.locationName}</span>
						</label>
					{/each}
				</div>
			{/if}
		</div>

		<select
			value={filterCondition}
			on:change={handleConditionChange}
			class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-primary-500 dark:focus:ring-primary-800"
		>
			{#each conditionOptions as option}
				<option value={option.value}>{option.label}</option>
			{/each}
		</select>

		<select
			value={filterSeasonal}
			on:change={handleSeasonalChange}
			class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-primary-500 dark:focus:ring-primary-800"
		>
			{#each seasonalOptions as option}
				<option value={option.value}>{option.label}</option>
			{/each}
		</select>

		<select
			value={filterOwner}
			on:change={handleOwnerChange}
			class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-primary-500 dark:focus:ring-primary-800"
		>
			<option value="">All Owners</option>
			<option value="unassigned">Unassigned</option>
			{#each users as user}
				<option value={user.id}>{user.name}</option>
			{/each}
		</select>

		<select
			value={filterNeedsReview === null ? '' : filterNeedsReview.toString()}
			on:change={handleNeedsReviewChange}
			class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:focus:border-primary-500 dark:focus:ring-primary-800"
		>
			<option value="">All Review Status</option>
			<option value="true">Needs Review</option>
			<option value="false">Reviewed</option>
		</select>

		{#if hasActiveFilters}
			<button
				class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
				on:click={clearAllFilters}
			>
				Clear all filters
			</button>
		{/if}
	</div>
</div>
