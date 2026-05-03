<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { triage, items as itemsApi } from '$lib/api';
	import { Card } from '$lib/components';
	import { _ } from '$lib/i18n';
	import type { DiscardGroup } from '$lib/api/triage';

	let loading = true;
	let groups: DiscardGroup[] = [];
	let total = 0;
	let busyItemId: string | null = null;

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await load();
	});

	async function load() {
		loading = true;
		try {
			const res = await triage.discardList();
			groups = res.groups;
			total = res.total;
		} catch {
			toast.error('Failed to load discard pile');
		} finally {
			loading = false;
		}
	}

	async function undo(itemId: string) {
		busyItemId = itemId;
		try {
			await triage.undo(itemId);
			toast.success('Decision cleared');
			await load();
		} catch {
			toast.error('Failed to undo');
		} finally {
			busyItemId = null;
		}
	}

	async function markDonated(itemId: string, name: string) {
		if (!confirm(`Mark "${name}" as donated and remove from inventory?`)) return;
		busyItemId = itemId;
		try {
			await triage.markDonated(itemId);
			toast.success('Marked donated');
			await load();
		} catch {
			toast.error('Failed to mark donated');
		} finally {
			busyItemId = null;
		}
	}

	async function deleteItem(itemId: string, name: string) {
		if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
		busyItemId = itemId;
		try {
			await itemsApi.deleteItem(itemId);
			toast.success('Deleted');
			await load();
		} catch {
			toast.error('Failed to delete');
		} finally {
			busyItemId = null;
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mb-6 flex flex-wrap items-end justify-between gap-4">
		<div>
			<h1 class="text-3xl font-bold text-slate-900 dark:text-white">Discard pile</h1>
			<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
				Items the household has decided to toss. Grouped by container so you can do a single sweep
				per shelf or box.
			</p>
		</div>
		<a href="/declutter" class="text-sm text-primary-600 hover:underline">
			← Back to declutter
		</a>
	</div>

	{#if loading}
		<div class="py-12 text-center text-slate-500">Loading…</div>
	{:else if total === 0}
		<Card>
			<div class="py-12 text-center">
				<p class="text-lg font-medium text-slate-700 dark:text-slate-200">Nothing to discard.</p>
				<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
					Items you mark as Toss on <a href="/declutter" class="text-primary-600 underline">/declutter</a> will collect here.
				</p>
			</div>
		</Card>
	{:else}
		<p class="mb-4 text-sm text-slate-500">
			{total} item{total === 1 ? '' : 's'} across {groups.length} container{groups.length === 1 ? '' : 's'}.
		</p>
		<div class="space-y-6">
			{#each groups as group (group.container_id)}
				<section>
					<h2 class="mb-3 text-lg font-semibold text-slate-900 dark:text-white">
						{group.path_label}
						<span class="ml-2 text-sm font-normal text-slate-500">
							{group.items.length} {group.items.length === 1 ? 'item' : 'items'}
						</span>
					</h2>
					<div class="grid gap-3">
						{#each group.items as item (item.id)}
							<Card>
								<div class="flex gap-4">
									{#if item.primary_image_url}
										<a href="/items/{item.id}" class="shrink-0">
											<img
												src={item.primary_image_url}
												alt={item.name}
												class="h-20 w-20 rounded-lg object-cover"
											/>
										</a>
									{:else}
										<div class="h-20 w-20 shrink-0 rounded-lg bg-slate-100 dark:bg-slate-700"></div>
									{/if}
									<div class="flex flex-1 flex-col justify-between">
										<div>
											<a
												href="/items/{item.id}"
												class="font-medium text-slate-900 hover:text-primary-600 dark:text-white"
											>
												{item.name}
											</a>
											<p class="mt-0.5 text-sm text-slate-500">
												{#if item.size}Size {item.size}{#if item.owner} · {/if}{/if}
												{#if item.owner}{item.owner.name}{/if}
											</p>
										</div>
									</div>
									<div class="flex shrink-0 flex-col items-end justify-center gap-2">
										<button
											type="button"
											disabled={busyItemId === item.id}
											on:click={() => deleteItem(item.id, item.name)}
											class="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
										>
											Delete
										</button>
										<button
											type="button"
											disabled={busyItemId === item.id}
											on:click={() => markDonated(item.id, item.name)}
											class="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
										>
											Donated
										</button>
										<button
											type="button"
											disabled={busyItemId === item.id}
											on:click={() => undo(item.id)}
											class="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
										>
											Undo
										</button>
									</div>
								</div>
							</Card>
						{/each}
					</div>
				</section>
			{/each}
		</div>
	{/if}
</div>
