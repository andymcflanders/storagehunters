<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { outgrown as outgrownApi, items as itemsApi } from '$lib/api';
	import { Button, Card } from '$lib/components';
	import { _ } from '$lib/i18n';
	import type { OutgrownItem } from '$lib/api/outgrown';

	let loading = true;
	let items: OutgrownItem[] = [];
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
			const res = await outgrownApi.listOutgrown();
			items = res.items;
		} catch {
			toast.error('Failed to load outgrown items');
		} finally {
			loading = false;
		}
	}

	function formatAge(months: number): string {
		if (months < 12) return `${months} mo`;
		const years = Math.floor(months / 12);
		const remaining = months % 12;
		if (remaining === 0) return `${years} yr`;
		return `${years} yr ${remaining} mo`;
	}

	function inheritLabel(item: OutgrownItem): string {
		if (!item.inherit_to) return '';
		const name = item.inherit_to.user.name;
		if (item.inherit_to.months_until_fit === 0) {
			return `Inherit to ${name} (fits now)`;
		}
		return `Inherit to ${name} (fits in ~${formatAge(item.inherit_to.months_until_fit)})`;
	}

	$: groupedByOwner = (() => {
		const map = new Map<string, { ownerName: string; items: OutgrownItem[] }>();
		for (const item of items) {
			const key = item.effective_owner.id;
			if (!map.has(key)) {
				map.set(key, { ownerName: item.effective_owner.name, items: [] });
			}
			map.get(key)!.items.push(item);
		}
		return Array.from(map.values());
	})();

	async function reassign(item: OutgrownItem) {
		if (!item.inherit_to) return;
		busyItemId = item.id;
		try {
			await itemsApi.updateItem(item.id, {
				owner_id: item.inherit_to.user.id,
				dismiss_outgrown: false
			});
			toast.success(`Reassigned to ${item.inherit_to.user.name}`);
			await load();
		} catch {
			toast.error('Failed to reassign');
		} finally {
			busyItemId = null;
		}
	}

	async function dismiss(item: OutgrownItem) {
		busyItemId = item.id;
		try {
			await itemsApi.updateItem(item.id, { dismiss_outgrown: true });
			items = items.filter((i) => i.id !== item.id);
		} catch {
			toast.error('Failed to dismiss');
		} finally {
			busyItemId = null;
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="mb-6">
		<h1 class="text-3xl font-bold text-slate-900 dark:text-white">{$_('nav.outgrown')}</h1>
		<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
			Items the household has aged out of, with inherit suggestions when another member fits the size.
		</p>
	</div>

	{#if loading}
		<div class="py-12 text-center text-slate-500">Loading…</div>
	{:else if items.length === 0}
		<Card>
			<div class="py-12 text-center">
				<p class="text-lg font-medium text-slate-700 dark:text-slate-200">Nothing outgrown.</p>
				<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
					When a household member ages past the size of an item they own, it will surface here.
				</p>
			</div>
		</Card>
	{:else}
		<div class="space-y-8">
			{#each groupedByOwner as group}
				<section>
					<h2 class="mb-3 text-lg font-semibold text-slate-900 dark:text-white">
						{group.ownerName}
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
												{#if item.size}Size {item.size} · {/if}
												Outgrown {formatAge(item.months_outgrown)} ago
												{#if item.is_suggested_owner}
													<span class="ml-2 rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-700 dark:bg-purple-900/40 dark:text-purple-200">
														AI-suggested owner
													</span>
												{/if}
											</p>
											{#if item.inherit_to}
												<p class="mt-1 text-sm text-emerald-700 dark:text-emerald-300">
													→ {inheritLabel(item)}
												</p>
											{/if}
										</div>
									</div>
									<div class="flex shrink-0 flex-col items-end justify-center gap-2">
										{#if item.inherit_to}
											<Button
												size="sm"
												loading={busyItemId === item.id}
												on:click={() => reassign(item)}
											>
												Reassign
											</Button>
										{/if}
										<Button
											size="sm"
											variant="secondary"
											loading={busyItemId === item.id}
											on:click={() => dismiss(item)}
										>
											Dismiss
										</Button>
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
