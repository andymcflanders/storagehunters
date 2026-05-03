<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { triage } from '$lib/api';
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
	let filtersOpen = false;

	// Swipe state. Pointer-events drive both touch and mouse drags so
	// we get the same code path on mobile and desktop.
	const COMMIT_THRESHOLD_PX = 120;
	let dragging = false;
	let startX = 0;
	let startY = 0;
	let dx = 0;
	let dy = 0;
	let exitDirection: 'left' | 'right' | 'up' | null = null;

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
		const itemId = current.id;
		try {
			await triage.decide(itemId, decision);
			reviewedThisSession += 1;
			dx = 0;
			dy = 0;
			exitDirection = null;
			await loadNext();
			loadFilters();
		} catch {
			toast.error('Failed to record decision');
			dx = 0;
			dy = 0;
			exitDirection = null;
		} finally {
			working = false;
		}
	}

	function onFilterChange() {
		loadNext();
	}

	function clearFilters() {
		selectedOwnerId = '';
		selectedTag = '';
		loadNext();
	}

	function onPointerDown(event: PointerEvent) {
		if (working || !current || exitDirection) return;
		const target = event.target as HTMLElement;
		if (target.closest('a, button, select, [data-no-swipe]')) return;

		dragging = true;
		startX = event.clientX;
		startY = event.clientY;
		(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
	}

	function onPointerMove(event: PointerEvent) {
		if (!dragging) return;
		dx = event.clientX - startX;
		dy = event.clientY - startY;
	}

	function onPointerUp(event: PointerEvent) {
		if (!dragging) return;
		dragging = false;
		(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);

		const absX = Math.abs(dx);
		const absY = Math.abs(dy);
		if (absX > COMMIT_THRESHOLD_PX && absX >= absY) {
			triggerExit(dx > 0 ? 'right' : 'left');
		} else if (dy < -COMMIT_THRESHOLD_PX && absY > absX) {
			triggerExit('up');
		} else {
			dx = 0;
			dy = 0;
		}
	}

	function triggerExit(direction: 'left' | 'right' | 'up') {
		exitDirection = direction;
		setTimeout(() => {
			if (direction === 'right') decide('love');
			else if (direction === 'left') decide('hate');
			else decide('undecided');
		}, 220);
	}

	$: cardStyle = (() => {
		if (exitDirection === 'right') {
			return 'transform: translate(150%, 0) rotate(20deg); opacity: 0; transition: transform 220ms ease-out, opacity 220ms ease-out;';
		}
		if (exitDirection === 'left') {
			return 'transform: translate(-150%, 0) rotate(-20deg); opacity: 0; transition: transform 220ms ease-out, opacity 220ms ease-out;';
		}
		if (exitDirection === 'up') {
			return 'transform: translate(0, -150%) scale(0.9); opacity: 0; transition: transform 220ms ease-out, opacity 220ms ease-out;';
		}
		const rotation = dx / 20;
		const transition = dragging ? 'none' : 'transform 200ms ease-out';
		return `transform: translate(${dx}px, ${dy}px) rotate(${rotation}deg); transition: ${transition};`;
	})();

	$: dragOpacity = Math.min(1, Math.max(Math.abs(dx), Math.abs(dy)) / COMMIT_THRESHOLD_PX);
	$: dominantDirection = (() => {
		if (!dragging && !exitDirection) return null;
		const absX = Math.abs(dx);
		const absY = Math.abs(dy);
		if (exitDirection) return exitDirection;
		if (absX > absY) return dx > 0 ? 'right' : 'left';
		if (dy < 0) return 'up';
		return null;
	})();

	$: filterCount = (selectedOwnerId ? 1 : 0) + (selectedTag ? 1 : 0);
</script>

<!--
  Fullbleed layout: the layout drops its main padding for /declutter
  so we own the entire area below the top header (and above the
  mobile bottom nav). Page itself never scrolls; only the card body
  scrolls when its details overflow.

  Height math:
    mobile  = 100dvh − 64px (sticky header) − 64px (fixed bottom nav)
    desktop = 100dvh − 64px (sticky header) − 48px (desktop nav row)
  Inline style to compose env() with arbitrary calc — Tailwind's
  arbitrary-value syntax doesn't accept parenthesised env().
-->
<div
	class="declutter-fullbleed flex flex-col overflow-hidden px-4 pt-3 pb-3 sm:px-6 lg:px-8"
>
	<!-- Header row: title + counter + filter toggle + discard link -->
	<div class="flex shrink-0 items-center justify-between gap-3 pb-2">
		<h1 class="text-xl font-bold text-slate-900 dark:text-white sm:text-2xl">
			{$_('nav.declutter')}
		</h1>
		<div class="flex items-center gap-2 text-sm">
			{#if reviewedThisSession > 0}
				<span class="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200">
					{reviewedThisSession}
				</span>
			{/if}
			<button
				type="button"
				on:click={() => (filtersOpen = !filtersOpen)}
				data-no-swipe
				class="flex items-center gap-1 rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
			>
				Filters
				{#if filterCount > 0}
					<span class="rounded-full bg-primary-100 px-1.5 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
						{filterCount}
					</span>
				{/if}
				<svg class="h-3 w-3 transition-transform {filtersOpen ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			<a
				href="/declutter/discard"
				data-no-swipe
				class="hidden rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800 sm:inline-block"
			>
				Discard pile →
			</a>
		</div>
	</div>

	<!-- Filter dropdown panel -->
	{#if filtersOpen}
		<div
			data-no-swipe
			class="mb-2 grid shrink-0 gap-2 rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800 sm:grid-cols-3"
		>
			<div>
				<label for="filter-owner" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Owner</label>
				<select
					id="filter-owner"
					bind:value={selectedOwnerId}
					on:change={onFilterChange}
					class="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700"
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
					class="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700"
				>
					<option value="">Any tag</option>
					{#each tags as t}
						<option value={t.id}>{t.label} ({t.count})</option>
					{/each}
				</select>
			</div>
			<div class="flex items-end justify-between gap-2 sm:justify-end">
				<a
					href="/declutter/discard"
					class="text-sm text-primary-600 hover:underline sm:hidden"
				>
					Discard pile →
				</a>
				{#if filterCount > 0}
					<button
						type="button"
						on:click={clearFilters}
						class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
					>
						Clear
					</button>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Card slot: flex-1 + overflow-hidden so the card itself never
	     pushes the page beyond the viewport. -->
	<div class="relative flex-1 overflow-hidden">
		{#if loading}
			<div class="flex h-full items-center justify-center text-slate-500">Loading…</div>
		{:else if current === null}
			<div class="flex h-full flex-col items-center justify-center text-center">
				<p class="text-lg font-medium text-slate-700 dark:text-slate-200">You're all caught up.</p>
				<p class="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
					{#if selectedOwnerId || selectedTag}
						Nothing matches the current filters. Try clearing them, or check back in a few months.
					{:else}
						Every item has been triaged. Come back when undecided items resurface.
					{/if}
				</p>
			</div>
		{:else}
			<div
				class="flex h-full touch-none select-none flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800"
				on:pointerdown={onPointerDown}
				on:pointermove={onPointerMove}
				on:pointerup={onPointerUp}
				on:pointercancel={onPointerUp}
				role="presentation"
				style={cardStyle}
			>
				<!-- Image: fixed proportion of the card height, never scrolls -->
				<div class="relative shrink-0 bg-slate-100 dark:bg-slate-700" style="height: 45%; min-height: 180px;">
					{#if current.primary_image_url}
						<img
							src={current.primary_image_url}
							alt={current.name}
							draggable="false"
							class="h-full w-full object-cover"
						/>
					{:else}
						<div class="flex h-full items-center justify-center text-slate-400">No image</div>
					{/if}

					{#if dominantDirection === 'right'}
						<div
							class="pointer-events-none absolute inset-0 flex items-start justify-end p-3"
							style="opacity: {dragOpacity}"
						>
							<span class="rotate-12 rounded-md border-4 border-emerald-500 bg-emerald-100/80 px-3 py-1 text-xl font-extrabold uppercase tracking-wider text-emerald-700">
								Love
							</span>
						</div>
					{:else if dominantDirection === 'left'}
						<div
							class="pointer-events-none absolute inset-0 flex items-start justify-start p-3"
							style="opacity: {dragOpacity}"
						>
							<span class="-rotate-12 rounded-md border-4 border-red-500 bg-red-100/80 px-3 py-1 text-xl font-extrabold uppercase tracking-wider text-red-700">
								Toss
							</span>
						</div>
					{:else if dominantDirection === 'up'}
						<div
							class="pointer-events-none absolute inset-0 flex items-end justify-center p-3"
							style="opacity: {dragOpacity}"
						>
							<span class="rounded-md border-4 border-amber-500 bg-amber-100/80 px-3 py-1 text-xl font-extrabold uppercase tracking-wider text-amber-700">
								Maybe
							</span>
						</div>
					{/if}
				</div>

				<!-- Details: scroll inside the card when info overflows -->
				<div class="flex-1 overflow-y-auto px-4 py-3" data-no-swipe>
					<a
						href="/items/{current.id}"
						class="text-xl font-bold text-slate-900 hover:text-primary-600 dark:text-white"
					>
						{current.name}
					</a>

					<div class="mt-1 space-y-0.5 text-sm text-slate-600 dark:text-slate-300">
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
						<p class="mt-2 text-sm text-slate-600 dark:text-slate-300">{current.description}</p>
					{/if}

					{#if current.tags.length > 0}
						<div class="mt-2 flex flex-wrap gap-1">
							{#each current.tags.slice(0, 12) as t}
								<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700 dark:bg-slate-700 dark:text-slate-200">
									{t.name}
								</span>
							{/each}
						</div>
					{/if}

					{#if current.previous_decision}
						<p class="mt-2 text-xs italic text-slate-500">
							Previously: {current.previous_decision}
						</p>
					{/if}

					<p class="mt-3 text-xs text-slate-400">
						{remaining} item{remaining === 1 ? '' : 's'} remaining
						<span class="ml-2 hidden sm:inline">· Swipe →&nbsp;Love · ↑&nbsp;Maybe · ←&nbsp;Toss</span>
					</p>
				</div>

				<!-- Action buttons: pinned to the bottom of the card -->
				<div class="grid shrink-0 grid-cols-3 gap-2 border-t border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800">
					<button
						type="button"
						on:click={() => decide('hate')}
						disabled={working}
						class="rounded-lg border border-red-200 bg-red-50 px-2 py-2.5 text-sm font-medium text-red-700 transition hover:bg-red-100 disabled:opacity-50 dark:border-red-900 dark:bg-red-900/20 dark:text-red-200 dark:hover:bg-red-900/40"
					>
						🗑️ Toss
					</button>
					<button
						type="button"
						on:click={() => decide('undecided')}
						disabled={working}
						class="rounded-lg border border-amber-200 bg-amber-50 px-2 py-2.5 text-sm font-medium text-amber-700 transition hover:bg-amber-100 disabled:opacity-50 dark:border-amber-900 dark:bg-amber-900/20 dark:text-amber-200 dark:hover:bg-amber-900/40"
					>
						🤔 Maybe
					</button>
					<button
						type="button"
						on:click={() => decide('love')}
						disabled={working}
						class="rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-2.5 text-sm font-medium text-emerald-700 transition hover:bg-emerald-100 disabled:opacity-50 dark:border-emerald-900 dark:bg-emerald-900/20 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
					>
						❤️ Love
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Height is set in CSS rather than inline so we can express
	   different values per breakpoint. The class is unique to this
	   page so the global selector is effectively scoped. */
	.declutter-fullbleed {
		height: calc(100dvh - 64px - 64px - env(safe-area-inset-bottom, 0px));
	}
	@media (min-width: 768px) {
		.declutter-fullbleed {
			height: calc(100dvh - 64px - 48px);
		}
	}
</style>
