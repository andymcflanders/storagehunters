<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { search } from '$lib/api';
	import { _ } from '$lib/i18n';
	import type { SearchResultItem } from '$lib/api/search';

	let searchQuery = '';
	let searchResults: SearchResultItem[] = [];
	let isSearching = false;

	async function handleSearch() {
		if (!searchQuery.trim()) {
			searchResults = [];
			return;
		}
		isSearching = true;
		try {
			const result = await search.autocomplete(searchQuery);
			searchResults = result.items;
		} catch (error) {
			toast.error('Search failed');
		} finally {
			isSearching = false;
		}
	}

	function goToSearch() {
		goto(`/search?q=${encodeURIComponent(searchQuery)}`);
	}

	function clearSearch() {
		searchQuery = '';
		searchResults = [];
	}

	// Debounce search
	let searchTimeout: ReturnType<typeof setTimeout>;
	$: {
		clearTimeout(searchTimeout);
		if (searchQuery.trim()) {
			searchTimeout = setTimeout(handleSearch, 150);
		} else {
			searchResults = [];
		}
	}
</script>

<div class="flex flex-col min-h-[60vh]">
	<!-- Header & Search -->
	<div class="space-y-4 px-1">
		<div>
			<h1 class="text-2xl font-bold text-slate-900 dark:text-white">
				Hi, {$user?.name?.split(' ')[0] || 'there'}!
			</h1>
			<p class="text-slate-500 dark:text-slate-400">{$_('mobile.searchPrompt')}</p>
		</div>

		<!-- Search Bar -->
		<div class="relative">
			<div class="relative">
				<svg class="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="search"
					placeholder={$_('mobile.searchPlaceholder')}
					class="w-full rounded-2xl border border-slate-200 bg-white py-4 pl-12 pr-12 text-base shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-primary-400"
					bind:value={searchQuery}
					on:keypress={(e) => e.key === 'Enter' && goToSearch()}
				/>
				{#if searchQuery}
					<button
						class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
						on:click={clearSearch}
					>
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				{/if}
			</div>

			<!-- Search Results Dropdown -->
			{#if searchQuery && (searchResults.length > 0 || isSearching)}
				<div class="absolute left-0 right-0 top-full z-50 mt-2 rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-800 overflow-hidden">
					{#if isSearching}
						<div class="p-6 text-center text-slate-500">
							<div class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
						</div>
					{:else}
						<div class="max-h-[50vh] overflow-y-auto">
							{#each searchResults as item}
								<a
									href="/items/{item.id}"
									class="flex items-center gap-3 border-b border-slate-100 p-4 last:border-0 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-700/50"
								>
									<div class="h-12 w-12 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-700">
										{#if item.thumbnail_url}
											<img src={item.thumbnail_url} alt="" class="h-full w-full object-cover" />
										{:else}
											<div class="flex h-full w-full items-center justify-center text-slate-400">
												<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
												</svg>
											</div>
										{/if}
									</div>
									<div class="flex-1 min-w-0">
										<p class="font-medium text-slate-900 dark:text-white truncate">{item.name}</p>
										<p class="text-sm text-slate-500 truncate">{item.path.map(p => p.name).join(' › ')}</p>
									</div>
									<svg class="h-5 w-5 flex-shrink-0 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
									</svg>
								</a>
							{/each}
						</div>
						<button
							class="w-full border-t border-slate-200 p-4 text-center text-sm font-medium text-primary-600 hover:bg-slate-50 dark:border-slate-700 dark:text-primary-400 dark:hover:bg-slate-700/50"
							on:click={goToSearch}
						>
							See all results for "{searchQuery}"
						</button>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	<!-- Empty State / Tips -->
	{#if !searchQuery}
		<div class="flex-1 flex flex-col items-center justify-center text-center px-6 py-12">
			<div class="flex h-20 w-20 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 mb-4">
				<svg class="h-10 w-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
			</div>
			<h3 class="text-lg font-medium text-slate-700 dark:text-slate-300">{$_('mobile.findAnything')}</h3>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400 max-w-xs">
				{$_('mobile.searchHelp')}
			</p>
			<div class="mt-6 flex flex-wrap justify-center gap-2">
				<button
					class="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
					on:click={() => { searchQuery = 'winter'; handleSearch(); }}
				>
					winter clothes
				</button>
				<button
					class="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
					on:click={() => { searchQuery = 'tools'; handleSearch(); }}
				>
					tools
				</button>
				<button
					class="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
					on:click={() => { searchQuery = 'electronics'; handleSearch(); }}
				>
					electronics
				</button>
			</div>
		</div>
	{:else if searchResults.length === 0 && !isSearching}
		<div class="flex-1 flex flex-col items-center justify-center text-center px-6 py-12">
			<div class="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 mb-4">
				<svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
			</div>
			<p class="text-slate-500 dark:text-slate-400">{$_('mobile.noResultsFor', { values: { query: searchQuery } })}</p>
			<p class="mt-1 text-sm text-slate-400">{$_('mobile.tryDifferent')}</p>
		</div>
	{/if}
</div>
