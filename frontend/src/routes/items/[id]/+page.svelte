<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { items } from '$lib/api';
	import { Breadcrumb, Button, Card, Input, Modal } from '$lib/components';
	import type { ItemWithDetails } from '$lib/types';

	let item: ItemWithDetails | null = null;
	let loading = true;
	let uploading = false;
	let showUploadModal = false;
	let fileInput: HTMLInputElement;

	$: itemId = $page.params.id;

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadItem();
	});

	async function loadItem() {
		loading = true;
		try {
			item = await items.getItem(itemId);
		} catch {
			toast.error('Item not found');
			goto('/');
		} finally {
			loading = false;
		}
	}

	async function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const files = target.files;
		if (!files || files.length === 0) return;

		uploading = true;
		try {
			for (const file of files) {
				await items.uploadItemImage(itemId, file);
			}
			toast.success('Image uploaded successfully');
			await loadItem();
		} catch (error) {
			toast.error('Failed to upload image');
		} finally {
			uploading = false;
			showUploadModal = false;
		}
	}

	async function deleteImage(imageId: string) {
		if (!confirm('Are you sure you want to delete this image?')) return;

		try {
			await items.deleteItemImage(itemId, imageId);
			toast.success('Image deleted');
			await loadItem();
		} catch {
			toast.error('Failed to delete image');
		}
	}

	function formatCondition(condition: string): string {
		return condition.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
	}
</script>

<svelte:head>
	<title>{item?.name ?? 'Item'} - StorageHub</title>
</svelte:head>

{#if loading}
	<div class="space-y-6">
		<div class="h-8 w-48 animate-pulse rounded bg-slate-200"></div>
		<div class="h-64 animate-pulse rounded-xl bg-slate-200"></div>
	</div>
{:else if item}
	<div class="space-y-6">
		<!-- Breadcrumb -->
		<Breadcrumb path={item.path} currentName={item.name} />

		<div class="grid gap-8 lg:grid-cols-2">
			<!-- Images -->
			<div>
				{#if item.images.length > 0}
					<div class="grid gap-4">
						{#each item.images as image, i}
							<div class="group relative overflow-hidden rounded-xl bg-slate-100">
								<img
									src={image.filepath}
									alt="{item.name} - Image {i + 1}"
									class="aspect-square w-full object-cover"
								/>
								<button
									class="absolute right-2 top-2 rounded-lg bg-red-600 p-2 text-white opacity-0 transition-opacity group-hover:opacity-100"
									on:click={() => deleteImage(image.id)}
								>
									<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>

								{#if image.ai_processed && image.ai_tags.length > 0}
									<div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
										<div class="flex flex-wrap gap-1">
											{#each image.ai_tags.slice(0, 5) as tag}
												<span class="rounded-full bg-white/20 px-2 py-0.5 text-xs text-white backdrop-blur">
													{tag}
												</span>
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<Card>
						<div class="py-12 text-center">
							<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
							<h3 class="mt-4 text-lg font-medium text-slate-900">No photos yet</h3>
							<p class="mt-2 text-slate-500">Add photos to help identify this item.</p>
						</div>
					</Card>
				{/if}

				<Button class="mt-4 w-full" variant="secondary" on:click={() => fileInput.click()}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
					</svg>
					{uploading ? 'Uploading...' : 'Add Photo'}
				</Button>
				<input
					type="file"
					accept="image/*"
					multiple
					class="hidden"
					bind:this={fileInput}
					on:change={handleFileSelect}
				/>
			</div>

			<!-- Details -->
			<div class="space-y-6">
				<div>
					<h1 class="text-2xl font-bold text-slate-900">{item.name}</h1>
					{#if item.description}
						<p class="mt-2 text-slate-600">{item.description}</p>
					{/if}
				</div>

				<Card>
					<h3 class="mb-4 font-semibold text-slate-900">Details</h3>
					<dl class="space-y-3">
						{#if item.owner}
							<div class="flex justify-between">
								<dt class="text-slate-500">Owner</dt>
								<dd class="font-medium text-slate-900">{item.owner.name}</dd>
							</div>
						{/if}
						<div class="flex justify-between">
							<dt class="text-slate-500">Condition</dt>
							<dd>
								<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
									{item.condition === 'good' ? 'bg-green-100 text-green-700' :
									 item.condition === 'fair' ? 'bg-yellow-100 text-yellow-700' :
									 item.condition === 'damaged' ? 'bg-red-100 text-red-700' :
									 'bg-orange-100 text-orange-700'}">
									{formatCondition(item.condition)}
								</span>
							</dd>
						</div>
						{#if item.size}
							<div class="flex justify-between">
								<dt class="text-slate-500">Size</dt>
								<dd class="font-medium text-slate-900">{item.size}</dd>
							</div>
						{/if}
						{#if item.seasonal !== 'none'}
							<div class="flex justify-between">
								<dt class="text-slate-500">Season</dt>
								<dd>
									<span class="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
										{item.seasonal}
									</span>
								</dd>
							</div>
						{/if}
						{#if item.value_estimate}
							<div class="flex justify-between">
								<dt class="text-slate-500">Est. Value</dt>
								<dd class="font-medium text-slate-900">${item.value_estimate}</dd>
							</div>
						{/if}
					</dl>
				</Card>

				{#if item.tags.length > 0}
					<Card>
						<h3 class="mb-4 font-semibold text-slate-900">Tags</h3>
						<div class="flex flex-wrap gap-2">
							{#each item.tags as tag}
								<span class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
									{tag.name}
								</span>
							{/each}
						</div>
					</Card>
				{/if}

				<div class="flex gap-2">
					<Button variant="secondary" class="flex-1">Edit</Button>
					<Button variant="danger">Delete</Button>
				</div>
			</div>
		</div>
	</div>
{/if}
