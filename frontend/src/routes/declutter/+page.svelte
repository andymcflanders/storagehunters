<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { triage } from '$lib/api';
	import { Card } from '$lib/components';
	import { _ } from '$lib/i18n';
	import type {
		TriageDecision,
		TriageFilterOption,
		TriageNextItem
	} from '$lib/api/triage';

	let loading = true;
	let working = false;
	let current: TriageNextItem | null = null;
	let remaining = 0;
	let reviewedThisSession = 0;

	let owners: TriageFilterOption[] = [];
	let tags: TriageFilterOption[] = [];
	let selectedOwnerId = '';
	let selectedTag = '';

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await Promise.all([loadFilters(), loadNext()]);
	});

	async function loadFilters() {
		try {
			const res = await triage.filters();
			owners = res.owners;
			tags = res.tags;
		} catch {
			// Filters are non-critical; the page still works without them.
		}
	}

	async function loadNext() {
		loading = true;
		try {
			const res = await triage.next({
				ownerId: selectedOwnerId || undefined,
				tag: selectedTag || undefined
			});
			current = res.item;
			remaining = res.remaining_estimate;
		} catch {
			toast.error('Failed to load next item');
		} finally {
			loading = false;
		}
	}

	async function decide(decision: TriageDecision) {
		if (!current || working) return;
		working = true;
		try {
			await triage.decide(current.id, decision);
			reviewedThisSession += 1;
			await loadNext();
			// Refresh filter counts in the background — they shift as
			// items move out of the eligible pool.
			loadFilters();
		} catch {
			toast.error('Failed to record decision');
		} finally {
			working = false;
		}
	}

	function onFilterChange() {
		loadNext();
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mb-6 flex flex-wrap items-end justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold text-slate-900 dark:text-white">{$_('nav.declutter')}</h1>
			<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
				One item at a time — Love it, can't decide, or out it goes. Loved items stay hidden for a year;
				undecideds come back in a few months.
			</p>
		</div>
		<div class="flex items-center gap-3 text-sm text-slate-500">
			{#if reviewedThisSession > 0}
				<span class="rounded-full bg-emerald-100 px-3 py-1 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200">
					{reviewedThisSession} reviewed
				</span>
			{/if}
			<a href="/declutter/discard" class="text-primary-600 hover:underline">
				Discard pile →
			</a>
		</div>
	</div>

	<!-- Filters -->
	<div class="mb-6 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800 sm:grid-cols-3">
		<div>
			<label for="filter-owner" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Owner</label>
			<select
				id="filter-owner"
				bind:value={selectedOwnerId}
				on:change={onFilterChange}
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700"
			>
				<option value="">Anyone</option>
				{#each owners as o}
					<option value={o.id}>{o.label} ({o.count})</option>
				{/each}
			</select>
		</div>
		<div>
			<label for="filter-tag" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Tag</label>
			<select
				id="filter-tag"
				bind:value={selectedTag}
				on:change={onFilterChange}
				class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700"
			>
				<option value="">Any tag</option>
				{#each tags as t}
					<option value={t.id}>{t.label} ({t.count})</option>
				{/each}
			</select>
		</div>
		<div class="flex items-end">
			{#if selectedOwnerId || selectedTag}
				<button
					type="button"
					on:click={() => {
						selectedOwnerId = '';
						selectedTag = '';
						loadNext();
					}}
					class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
				>
					Clear filters
				</button>
			{/if}
		</div>
	</div>

	{#if loading}
		<div class="py-12 text-center text-slate-500">Loading…</div>
	{:else if current === null}
		<Card>
			<div class="py-12 text-center">
				<p class="text-lg font-medium text-slate-700 dark:text-slate-200">You're all caught up.</p>
				<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
					{#if selectedOwnerId || selectedTag}
						Nothing matches the current filters. Try clearing them, or check back in a few months.
					{:else}
						Every item has been triaged. Come back in a few months when undecided items resurface.
					{/if}
				</p>
			</div>
		</Card>
	{:else}
		<Card>
			<div class="grid gap-6 md:grid-cols-2">
				<!-- Image -->
				<div class="aspect-square overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-700">
					{#if current.primary_image_url}
						<img
							src={current.primary_image_url}
							alt={current.name}
							class="h-full w-full object-cover"
						/>
					{:else}
						<div class="flex h-full items-center justify-center text-slate-400">No image</div>
					{/if}
				</div>

				<!-- Details -->
				<div class="flex flex-col">
					<a
						href="/items/{current.id}"
						class="text-2xl font-bold text-slate-900 hover:text-primary-600 dark:text-white"
					>
						{current.name}
					</a>

					<div class="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-300">
						{#if current.owner}
							<p><span class="font-medium">Owner:</span> {current.owner.name}</p>
						{/if}
						{#if current.size}
							<p><span class="font-medium">Size:</span> {current.size}</p>
						{/if}
						{#if current.path.length > 0}
							<p>
								<span class="font-medium">Where:</span>
								{current.path.map((p) => p.name).join(' / ')}
							</p>
						{/if}
					</div>

					{#if current.description}
						<p class="mt-3 text-sm text-slate-600 dark:text-slate-300">{current.description}</p>
					{/if}

					{#if current.tags.length > 0}
						<div class="mt-3 flex flex-wrap gap-1">
							{#each current.tags.slice(0, 10) as t}
								<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700 dark:bg-slate-700 dark:text-slate-200">
									{t.name}
								</span>
							{/each}
						</div>
					{/if}

					{#if current.previous_decision}
						<p class="mt-3 text-xs italic text-slate-500">
							Previously: {current.previous_decision}
						</p>
					{/if}

					<div class="mt-auto pt-6 text-xs text-slate-400">
						{remaining} item{remaining === 1 ? '' : 's'} remaining
					</div>
				</div>
			</div>

			<!-- Action buttons -->
			<div class="mt-6 grid grid-cols-3 gap-3 border-t border-slate-200 pt-6 dark:border-slate-700">
				<button
					type="button"
					on:click={() => decide('hate')}
					disabled={working}
					class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 font-medium text-red-700 transition hover:bg-red-100 disabled:opacity-50 dark:border-red-900 dark:bg-red-900/20 dark:text-red-200 dark:hover:bg-red-900/40"
				>
					🗑️ Toss
				</button>
				<button
					type="button"
					on:click={() => decide('undecided')}
					disabled={working}
					class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 font-medium text-amber-700 transition hover:bg-amber-100 disabled:opacity-50 dark:border-amber-900 dark:bg-amber-900/20 dark:text-amber-200 dark:hover:bg-amber-900/40"
				>
					🤔 Undecided
				</button>
				<button
					type="button"
					on:click={() => decide('love')}
					disabled={working}
					class="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 font-medium text-emerald-700 transition hover:bg-emerald-100 disabled:opacity-50 dark:border-emerald-900 dark:bg-emerald-900/20 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
				>
					❤️ Love
				</button>
			</div>
		</Card>
	{/if}
</div>
