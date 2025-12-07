<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { items } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import { locale } from '$lib/i18n';
	import { getLocalizedAI } from '$lib/utils/localized';
	import type { ItemWithDetails } from '$lib/types';
	import { Button } from '$lib/components';

	let loading = true;
	let pendingItems: ItemWithDetails[] = [];
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	onMount(async () => {
		await loadPendingItems();
		// Poll for updates every 5 seconds
		pollInterval = setInterval(loadPendingItems, 5000);
	});

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});

	async function loadPendingItems() {
		try {
			pendingItems = await items.getPendingReviewItems();
		} catch {
			if (loading) {
				toast.error('Failed to load pending items');
			}
		} finally {
			loading = false;
		}
	}

	async function confirmItem(item: ItemWithDetails) {
		try {
			await items.confirmItemReview(item.id);
			toast.success('Item confirmed');
			pendingItems = pendingItems.filter((i) => i.id !== item.id);
		} catch {
			toast.error('Failed to confirm item');
		}
	}

	async function confirmAll() {
		const toConfirm = [...pendingItems];
		for (const item of toConfirm) {
			try {
				await items.confirmItemReview(item.id);
				pendingItems = pendingItems.filter((i) => i.id !== item.id);
			} catch {
				toast.error(`Failed to confirm ${item.name || 'item'}`);
			}
		}
		if (pendingItems.length === 0) {
			toast.success('All items confirmed');
		}
	}

	async function deleteItem(item: ItemWithDetails) {
		if (!confirm(`Delete "${item.name || 'Unnamed item'}"?`)) return;
		try {
			await items.deleteItem(item.id);
			toast.success('Item deleted');
			pendingItems = pendingItems.filter((i) => i.id !== item.id);
		} catch {
			toast.error('Failed to delete item');
		}
	}

	function viewItem(item: ItemWithDetails) {
		goto(`/items/${item.id}`);
	}

	function getImageUrl(item: ItemWithDetails): string | null {
		if (item.images && item.images.length > 0) {
			return `/uploads/${item.images[0].filepath}`;
		}
		return null;
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const minutes = Math.floor(diff / 60000);
		const hours = Math.floor(diff / 3600000);

		if (minutes < 1) return 'Just now';
		if (minutes < 60) return `${minutes}m ago`;
		if (hours < 24) return `${hours}h ago`;
		return date.toLocaleDateString();
	}
</script>

<svelte:head>
	<title>Review Items - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Review Items</h1>
			<p class="mt-1 text-slate-500 dark:text-slate-400">
				{#if pendingItems.length > 0}
					{pendingItems.length} item{pendingItems.length !== 1 ? 's' : ''} need{pendingItems.length === 1 ? 's' : ''} review
				{:else}
					No items pending review
				{/if}
			</p>
		</div>
		{#if pendingItems.length > 0}
			<Button on:click={confirmAll}>
				<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
				Confirm All
			</Button>
		{/if}
	</div>

	<!-- Items List -->
	{#if loading}
		<div class="flex justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
		</div>
	{:else if pendingItems.length === 0}
		<div class="rounded-xl bg-white p-12 text-center shadow-sm dark:bg-slate-800">
			<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
				<svg class="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
			</div>
			<h2 class="mt-4 text-lg font-semibold text-slate-900 dark:text-white">All caught up!</h2>
			<p class="mt-2 text-slate-500 dark:text-slate-400">
				No items need review. New items from multi-item detection will appear here.
			</p>
			<button
				on:click={() => goto('/')}
				class="btn-primary mt-6"
			>
				Go Home
			</button>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each pendingItems as item}
				<div class="rounded-xl bg-white shadow-sm dark:bg-slate-800 overflow-hidden">
					<!-- Image -->
					<div class="relative aspect-square bg-slate-100 dark:bg-slate-700">
						{#if getImageUrl(item)}
							<img
								src={getImageUrl(item)}
								alt={item.name}
								class="h-full w-full object-contain"
							/>
						{:else}
							<div class="flex h-full items-center justify-center">
								<svg class="h-12 w-12 text-slate-300 dark:text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
							</div>
						{/if}

						<!-- AI badge -->
						{#if item.ai_processed}
							<div class="absolute top-2 left-2 rounded-full bg-primary-100 px-2 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/50 dark:text-primary-300">
								AI analyzed
							</div>
						{:else}
							<div class="absolute top-2 left-2 flex items-center gap-1.5 rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">
								<div class="h-2 w-2 animate-pulse rounded-full bg-amber-500"></div>
								Analyzing...
							</div>
						{/if}

						<!-- Time badge -->
						<div class="absolute top-2 right-2 rounded-full bg-slate-900/60 px-2 py-1 text-xs text-white">
							{formatDate(item.created_at)}
						</div>
					</div>

					<!-- Content -->
					<div class="p-4">
						<h3 class="font-medium text-slate-900 dark:text-white">
							{getLocalizedAI(item.ai_name, item.ai_name_no) || item.name || 'Unnamed item'}
						</h3>
						{#if getLocalizedAI(item.ai_description, item.ai_description_no)}
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
								{getLocalizedAI(item.ai_description, item.ai_description_no)}
							</p>
						{/if}

						<!-- Path -->
						{#if item.path && item.path.length > 0}
							<p class="mt-2 text-xs text-slate-400 dark:text-slate-500">
								{item.path.map(p => p.name).join(' > ')}
							</p>
						{/if}

						<!-- Actions -->
						<div class="mt-4 flex gap-2">
							<Button variant="secondary" class="flex-1" on:click={() => viewItem(item)}>
								<svg class="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
								</svg>
								Edit
							</Button>
							<Button class="flex-1" on:click={() => confirmItem(item)}>
								<svg class="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
								Confirm
							</Button>
							<button
								on:click={() => deleteItem(item)}
								class="rounded-lg p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
								title="Delete item"
							>
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
