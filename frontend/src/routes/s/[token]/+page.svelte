<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { shares } from '$lib/api';
	import type { PublicShareResponse } from '$lib/api/shares';

	let loading = true;
	let error = '';
	let data: PublicShareResponse | null = null;

	$: token = $page.params.token!;

	onMount(async () => {
		await loadShare();
	});

	async function loadShare() {
		loading = true;
		error = '';
		try {
			data = await shares.getPublicShare(token);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load share';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{data?.container.name || 'Shared Container'} - StorageHub</title>
</svelte:head>

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
	<!-- Simple header for public view -->
	<header class="border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
		<div class="mx-auto flex h-14 max-w-3xl items-center px-4">
			<div class="flex items-center gap-2">
				<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
						/>
					</svg>
				</div>
				<span class="text-lg font-bold text-slate-900 dark:text-white">StorageHub</span>
			</div>
			<span class="ml-3 rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700 dark:bg-primary-900 dark:text-primary-300">
				Shared View
			</span>
		</div>
	</header>

	<main class="mx-auto max-w-3xl px-4 py-8">
		{#if loading}
			<div class="flex flex-col items-center justify-center py-16">
				<div class="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
				<p class="mt-4 text-slate-500 dark:text-slate-400">Loading shared container...</p>
			</div>
		{:else if error}
			<div class="rounded-xl bg-white p-8 text-center shadow-sm dark:bg-slate-800">
				<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
					<svg class="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
					</svg>
				</div>
				<h1 class="mt-4 text-xl font-bold text-slate-900 dark:text-white">Unable to Load</h1>
				<p class="mt-2 text-slate-500 dark:text-slate-400">{error}</p>
			</div>
		{:else if data}
			<!-- Container Info -->
			<div class="rounded-xl bg-white p-6 shadow-sm dark:bg-slate-800">
				<div class="flex items-start gap-4">
					<div class="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-400">
						<svg class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
						</svg>
					</div>
					<div class="flex-1">
						<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{data.container.name}</h1>
						<p class="mt-1 flex items-center gap-1 text-slate-500 dark:text-slate-400">
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
							{data.container.location_name}
						</p>
						{#if data.container.notes}
							<p class="mt-3 text-slate-600 dark:text-slate-300">{data.container.notes}</p>
						{/if}
					</div>
				</div>

				<div class="mt-4 flex items-center gap-2 border-t border-slate-200 pt-4 dark:border-slate-700">
					<span class="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 dark:bg-slate-700 dark:text-slate-300">
						{data.container.item_count} {data.container.item_count === 1 ? 'item' : 'items'}
					</span>
				</div>
			</div>

			<!-- Items List -->
			{#if data.items}
				<div class="mt-6">
					<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Items in this container</h2>

					{#if data.items.length === 0}
						<div class="rounded-xl bg-white p-8 text-center shadow-sm dark:bg-slate-800">
							<p class="text-slate-500 dark:text-slate-400">This container is empty.</p>
						</div>
					{:else}
						<div class="space-y-3">
							{#each data.items as item}
								<div class="flex items-center gap-4 rounded-xl bg-white p-4 shadow-sm dark:bg-slate-800">
									{#if item.image_url}
										<img
											src={item.image_url}
											alt={item.name}
											class="h-16 w-16 flex-shrink-0 rounded-lg object-cover"
										/>
									{:else}
										<div class="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
											<svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
											</svg>
										</div>
									{/if}
									<div class="flex-1 min-w-0">
										<h3 class="font-medium text-slate-900 dark:text-white truncate">{item.name}</h3>
										{#if item.description}
											<p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400 line-clamp-2">{item.description}</p>
										{/if}
									</div>
									<div class="flex-shrink-0 text-right">
										<span class="text-sm font-medium text-slate-600 dark:text-slate-300">Qty: {item.quantity}</span>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{:else}
				<div class="mt-6 rounded-xl bg-slate-100 p-4 text-center text-sm text-slate-600 dark:bg-slate-800 dark:text-slate-400">
					Item details are not available for this shared link.
				</div>
			{/if}
		{/if}
	</main>

	<!-- Footer -->
	<footer class="mt-12 border-t border-slate-200 bg-white py-6 dark:border-slate-700 dark:bg-slate-900">
		<div class="mx-auto max-w-3xl px-4 text-center">
			<p class="text-sm text-slate-500 dark:text-slate-400">
				Shared via <span class="font-medium text-primary-600">StorageHub</span>
			</p>
		</div>
	</footer>
</div>
