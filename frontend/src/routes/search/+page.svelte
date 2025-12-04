<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { ItemCard, Card, Input } from '$lib/components';

	let query = '';
	let results: any[] = [];
	let loading = false;

	$: queryParam = $page.url.searchParams.get('q') || '';

	onMount(() => {
		if (!$user) {
			goto('/login');
			return;
		}

		query = queryParam;
		if (query) {
			search();
		}
	});

	async function search() {
		if (!query.trim()) return;

		loading = true;
		// TODO: Implement search API call
		loading = false;
	}

	function handleSubmit() {
		goto(`/search?q=${encodeURIComponent(query)}`);
		search();
	}
</script>

<svelte:head>
	<title>Search - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-slate-900">Search</h1>
		<p class="mt-1 text-slate-500">Find items across all your storage locations</p>
	</div>

	<form on:submit|preventDefault={handleSubmit}>
		<Input
			type="search"
			placeholder="Search for items..."
			bind:value={query}
		/>
	</form>

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
				<h3 class="mt-4 text-lg font-medium text-slate-900">No results found</h3>
				<p class="mt-2 text-slate-500">Try searching with different keywords</p>
			</div>
		</Card>
	{:else if results.length > 0}
		<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
			{#each results as item}
				<ItemCard {item} />
			{/each}
		</div>
	{:else}
		<Card>
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<h3 class="mt-4 text-lg font-medium text-slate-900">Search for items</h3>
				<p class="mt-2 text-slate-500">Enter a search term to find items by name, description, or tags</p>
			</div>
		</Card>
	{/if}
</div>
