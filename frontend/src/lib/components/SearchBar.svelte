<script lang="ts">
	import { goto } from '$app/navigation';
	import { search } from '$lib/api';
	import type { SearchResultItem } from '$lib/api/search';

	export let value = '';
	export let placeholder = 'Search items...';

	let searchResults: SearchResultItem[] = [];
	let isSearching = false;
	let showDropdown = false;

	async function handleAutocomplete() {
		if (!value.trim()) {
			searchResults = [];
			showDropdown = false;
			return;
		}
		isSearching = true;
		try {
			const result = await search.autocomplete(value);
			searchResults = result.items;
			showDropdown = true;
		} catch (error) {
			searchResults = [];
		} finally {
			isSearching = false;
		}
	}

	function handleSubmit() {
		showDropdown = false;
		if (value.trim()) {
			goto(`/search?q=${encodeURIComponent(value.trim())}`);
		}
	}

	function clearSearch() {
		value = '';
		searchResults = [];
		showDropdown = false;
	}

	function handleBlur() {
		// Delay to allow click on results
		setTimeout(() => {
			showDropdown = false;
		}, 200);
	}

	function handleFocus() {
		if (searchResults.length > 0) {
			showDropdown = true;
		}
	}

	// Debounce autocomplete
	let searchTimeout: ReturnType<typeof setTimeout>;
	$: {
		clearTimeout(searchTimeout);
		if (value.trim()) {
			searchTimeout = setTimeout(handleAutocomplete, 150);
		} else {
			searchResults = [];
			showDropdown = false;
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit} class="relative w-full max-w-md">
	<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
		<svg class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
			/>
		</svg>
	</div>
	<input
		type="search"
		bind:value
		{placeholder}
		class="input pl-10 pr-10"
		on:blur={handleBlur}
		on:focus={handleFocus}
	/>
	{#if value}
		<button
			type="button"
			class="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600"
			on:click={clearSearch}
		>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>
	{/if}

	<!-- Autocomplete Dropdown -->
	{#if showDropdown && (searchResults.length > 0 || isSearching)}
		<div class="absolute left-0 right-0 top-full z-50 mt-2 rounded-xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-800 overflow-hidden">
			{#if isSearching}
				<div class="p-4 text-center text-slate-500">
					<div class="inline-block h-5 w-5 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
				</div>
			{:else}
				<div class="max-h-80 overflow-y-auto">
					{#each searchResults as item}
						<a
							href="/items/{item.id}"
							class="flex items-center gap-3 border-b border-slate-100 p-3 last:border-0 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-700/50"
						>
							<div class="h-10 w-10 flex-shrink-0 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-700">
								{#if item.thumbnail_url}
									<img src={item.thumbnail_url} alt="" class="h-full w-full object-cover" />
								{:else}
									<div class="flex h-full w-full items-center justify-center text-slate-400">
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
										</svg>
									</div>
								{/if}
							</div>
							<div class="flex-1 min-w-0">
								<p class="font-medium text-slate-900 dark:text-white truncate text-sm">{item.name}</p>
								<p class="text-xs text-slate-500 truncate">{item.path.map(p => p.name).join(' › ')}</p>
							</div>
							<svg class="h-4 w-4 flex-shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</a>
					{/each}
				</div>
				<button
					type="button"
					class="w-full border-t border-slate-200 p-3 text-center text-sm font-medium text-primary-600 hover:bg-slate-50 dark:border-slate-700 dark:text-primary-400 dark:hover:bg-slate-700/50"
					on:click={handleSubmit}
				>
					See all results for "{value}"
				</button>
			{/if}
		</div>
	{/if}
</form>
