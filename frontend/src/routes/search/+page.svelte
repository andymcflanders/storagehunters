<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { search, locations, users } from '$lib/api';
	import { Card, Input, Button } from '$lib/components';
	import type { SearchResultItem, SearchFilters } from '$lib/api/search';
	import type { Location, User, Condition, Seasonal } from '$lib/types';

	let query = '';
	let results: SearchResultItem[] = [];
	let total = 0;
	let loading = false;
	let showFilters = false;

	// Filter options
	let locationList: Location[] = [];
	let userList: User[] = [];

	// Active filters
	let filters: SearchFilters = {};

	$: queryParam = $page.url.searchParams.get('q') || '';

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		// Load filter options
		try {
			[locationList, userList] = await Promise.all([
				locations.listLocations(),
				users.listUsers()
			]);
		} catch (e) {
			console.error('Failed to load filter options', e);
		}

		query = queryParam;
		if (query) {
			filters.q = query;
			await performSearch();
		}
	});

	async function performSearch() {
		loading = true;
		try {
			const result = await search.searchItems(filters);
			results = result.items;
			total = result.total;
		} catch (error) {
			toast.error('Search failed');
			results = [];
			total = 0;
		} finally {
			loading = false;
		}
	}

	function handleSubmit() {
		filters.q = query;
		goto(`/search?q=${encodeURIComponent(query)}`);
		performSearch();
	}

	function clearFilters() {
		filters = { q: query };
		performSearch();
	}

	function applyFilters() {
		performSearch();
	}

	const conditions: { value: Condition; label: string }[] = [
		{ value: 'good', label: 'Good' },
		{ value: 'fair', label: 'Fair' },
		{ value: 'damaged', label: 'Damaged' },
		{ value: 'needs_repair', label: 'Needs Repair' }
	];

	const seasons: { value: Seasonal; label: string }[] = [
		{ value: 'none', label: 'None' },
		{ value: 'spring', label: 'Spring' },
		{ value: 'summer', label: 'Summer' },
		{ value: 'fall', label: 'Fall' },
		{ value: 'winter', label: 'Winter' },
		{ value: 'holiday', label: 'Holiday' }
	];
</script>

<svelte:head>
	<title>Search - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Search</h1>
		<p class="mt-1 text-slate-500 dark:text-slate-400">Find items across all your storage locations</p>
	</div>

	<!-- Search Bar -->
	<form on:submit|preventDefault={handleSubmit} class="flex gap-2">
		<div class="flex-1">
			<Input
				type="search"
				placeholder="Search for items by name, description, or tags..."
				bind:value={query}
			/>
		</div>
		<Button type="submit">Search</Button>
		<Button variant="secondary" on:click={() => (showFilters = !showFilters)}>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
			</svg>
		</Button>
	</form>

	<!-- Filters Panel -->
	{#if showFilters}
		<Card>
			<h3 class="mb-4 font-semibold text-slate-900 dark:text-white">Filters</h3>
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<!-- Location Filter -->
				<div>
					<label class="label" for="filter-location">Location</label>
					<select
						id="filter-location"
						class="input"
						bind:value={filters.location}
					>
						<option value={undefined}>All Locations</option>
						{#each locationList as loc}
							<option value={loc.id}>{loc.name}</option>
						{/each}
					</select>
				</div>

				<!-- Owner Filter -->
				<div>
					<label class="label" for="filter-owner">Owner</label>
					<select
						id="filter-owner"
						class="input"
						bind:value={filters.owner}
					>
						<option value={undefined}>All Owners</option>
						{#each userList as u}
							<option value={u.id}>{u.name}</option>
						{/each}
					</select>
				</div>

				<!-- Condition Filter -->
				<div>
					<label class="label" for="filter-condition">Condition</label>
					<select
						id="filter-condition"
						class="input"
						bind:value={filters.condition}
					>
						<option value={undefined}>Any Condition</option>
						{#each conditions as cond}
							<option value={cond.value}>{cond.label}</option>
						{/each}
					</select>
				</div>

				<!-- Season Filter -->
				<div>
					<label class="label" for="filter-season">Season</label>
					<select
						id="filter-season"
						class="input"
						bind:value={filters.seasonal}
					>
						<option value={undefined}>Any Season</option>
						{#each seasons as s}
							<option value={s.value}>{s.label}</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="mt-4 flex justify-end gap-2">
				<Button variant="ghost" on:click={clearFilters}>Clear Filters</Button>
				<Button on:click={applyFilters}>Apply Filters</Button>
			</div>
		</Card>
	{/if}

	<!-- Results -->
	{#if loading}
		<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
			{#each [1, 2, 3, 4, 5, 6, 7, 8] as _}
				<div class="aspect-square animate-pulse rounded-xl bg-slate-200"></div>
			{/each}
		</div>
	{:else if queryParam && results.length === 0}
		<Card>
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">No results found</h3>
				<p class="mt-2 text-slate-500 dark:text-slate-400">Try searching with different keywords or adjusting your filters</p>
			</div>
		</Card>
	{:else if results.length > 0}
		<div class="flex items-center justify-between">
			<p class="text-sm text-slate-500 dark:text-slate-400">
				Found <strong>{total}</strong> {total === 1 ? 'item' : 'items'}
			</p>
		</div>

		<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
			{#each results as item}
				<a href="/items/{item.id}" class="block">
					<Card hover padding="none">
						<!-- Thumbnail -->
						<div class="aspect-square w-full overflow-hidden rounded-t-xl bg-slate-100 dark:bg-slate-700">
							{#if item.thumbnail_url}
								<img src={item.thumbnail_url} alt={item.name} class="h-full w-full object-cover" />
							{:else}
								<div class="flex h-full w-full items-center justify-center">
									<svg class="h-12 w-12 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
									</svg>
								</div>
							{/if}
						</div>

						<!-- Content -->
						<div class="p-4">
							<h3 class="font-medium text-slate-900 dark:text-white line-clamp-1">{item.name}</h3>

							<!-- Path -->
							<p class="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
								{item.path.map(p => p.name).join(' > ')}
							</p>

							<!-- Matching Tags -->
							{#if item.matching_tags.length > 0}
								<div class="mt-2 flex flex-wrap gap-1">
									{#each item.matching_tags.slice(0, 3) as tag}
										<span class="inline-flex items-center rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700 dark:text-primary-300">
											{tag}
										</span>
									{/each}
								</div>
							{/if}
						</div>
					</Card>
				</a>
			{/each}
		</div>
	{:else}
		<Card>
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">Search for items</h3>
				<p class="mt-2 text-slate-500 dark:text-slate-400">Enter a search term to find items by name, description, or tags</p>
			</div>
		</Card>
	{/if}
</div>
