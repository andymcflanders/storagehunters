<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { shares } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import type { ShareLink } from '$lib/api/shares';

	export let containerId: string;
	export let containerName: string;

	const dispatch = createEventDispatcher();

	let shareLinks: ShareLink[] = [];
	let loading = true;
	let creating = false;

	// Create form
	let allowItemView = true;
	let expiresInDays: number | null = null;

	const expirationOptions = [
		{ value: null, label: 'Never expires' },
		{ value: 1, label: '1 day' },
		{ value: 7, label: '7 days' },
		{ value: 30, label: '30 days' },
		{ value: 90, label: '90 days' }
	];

	async function loadShareLinks() {
		loading = true;
		try {
			const response = await shares.listShareLinks(containerId);
			shareLinks = response.items;
		} catch {
			toast.error('Failed to load share links');
		} finally {
			loading = false;
		}
	}

	async function handleCreate() {
		creating = true;
		try {
			await shares.createShareLink({
				container_id: containerId,
				allow_item_view: allowItemView,
				expires_in_days: expiresInDays
			});
			toast.success('Share link created');
			await loadShareLinks();
		} catch {
			toast.error('Failed to create share link');
		} finally {
			creating = false;
		}
	}

	async function handleToggle(link: ShareLink) {
		try {
			await shares.toggleShareLink(link.id);
			toast.success(link.is_active ? 'Link deactivated' : 'Link activated');
			await loadShareLinks();
		} catch {
			toast.error('Failed to toggle link');
		}
	}

	async function handleDelete(link: ShareLink) {
		if (!confirm('Delete this share link?')) return;
		try {
			await shares.deleteShareLink(link.id);
			toast.success('Share link deleted');
			await loadShareLinks();
		} catch {
			toast.error('Failed to delete share link');
		}
	}

	function copyLink(link: ShareLink) {
		const url = `${window.location.origin}${link.share_url}`;
		navigator.clipboard.writeText(url);
		toast.success('Link copied to clipboard');
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString();
	}

	function close() {
		dispatch('close');
	}

	// Load on mount
	loadShareLinks();
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" on:click|self={close}>
	<div class="w-full max-w-lg rounded-xl bg-white shadow-xl dark:bg-slate-800">
		<!-- Header -->
		<div class="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
			<div>
				<h2 class="text-lg font-semibold text-slate-900 dark:text-white">Share Container</h2>
				<p class="text-sm text-slate-500 dark:text-slate-400">{containerName}</p>
			</div>
			<button
				on:click={close}
				class="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700"
			>
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="max-h-[60vh] overflow-y-auto p-6">
			<!-- Create new link -->
			<div class="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
				<h3 class="font-medium text-slate-900 dark:text-white">Create new share link</h3>

				<div class="mt-4 space-y-3">
					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							bind:checked={allowItemView}
							class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400 focus:ring-primary-500"
						/>
						<span class="text-sm text-slate-700 dark:text-slate-300">Allow viewing items in container</span>
					</label>

					<div>
						<label class="label" for="expiration">Link expiration</label>
						<select id="expiration" bind:value={expiresInDays} class="input">
							{#each expirationOptions as option}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</div>

					<button
						on:click={handleCreate}
						disabled={creating}
						class="btn-primary w-full"
					>
						{creating ? 'Creating...' : 'Create Share Link'}
					</button>
				</div>
			</div>

			<!-- Existing links -->
			{#if loading}
				<div class="mt-6 flex justify-center py-8">
					<div class="h-6 w-6 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600"></div>
				</div>
			{:else if shareLinks.length > 0}
				<div class="mt-6">
					<h3 class="mb-3 font-medium text-slate-900 dark:text-white">Existing links</h3>
					<div class="space-y-3">
						{#each shareLinks as link}
							<div class="rounded-lg border border-slate-200 p-3 dark:border-slate-700 {!link.is_active ? 'opacity-60' : ''}">
								<div class="flex items-center justify-between">
									<div class="flex-1 min-w-0">
										<code class="block truncate text-sm text-slate-600 dark:text-slate-400">
											{link.share_url}
										</code>
										<div class="mt-1 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
											<span>{link.view_count} views</span>
											{#if link.expires_at}
												<span>Expires {formatDate(link.expires_at)}</span>
											{:else}
												<span>Never expires</span>
											{/if}
											{#if !link.allow_item_view}
												<span class="text-amber-600">Items hidden</span>
											{/if}
										</div>
									</div>

									<div class="flex items-center gap-1">
										<button
											on:click={() => copyLink(link)}
											class="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700"
											title="Copy link"
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
											</svg>
										</button>
										<button
											on:click={() => handleToggle(link)}
											class="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700"
											title={link.is_active ? 'Deactivate' : 'Activate'}
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												{#if link.is_active}
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
												{:else}
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
												{/if}
											</svg>
										</button>
										<button
											on:click={() => handleDelete(link)}
											class="rounded p-1.5 text-red-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
											title="Delete"
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
										</button>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
