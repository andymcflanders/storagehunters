<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { items, users } from '$lib/api';
	import { Breadcrumb, Button, Card, Input, Modal } from '$lib/components';
	import { _, locale } from '$lib/i18n';
	import { getLocalizedAI } from '$lib/utils/localized';
	import { CONDITION_KEYS, SEASONAL_KEYS } from '$lib/utils/itemEnums';
	import type { ItemWithDetails, ItemUpdate, User, Condition, Seasonal } from '$lib/types';

	let item: ItemWithDetails | null = null;
	let loading = true;
	let uploading = false;
	let saving = false;
	let deleting = false;
	let fileInput: HTMLInputElement;

	// Language toggle for AI content (null = use user preference)
	let contentLanguage: string | null = null;

	// Edit mode
	let editMode = false;
	let editData: ItemUpdate = {};

	// Get effective language for content display.
	$: effectiveLanguage = contentLanguage || $locale || 'en';

	// Localized AI content
	$: localizedName = item ? getLocalizedAI(item.ai_names, effectiveLanguage) : '';
	$: localizedDescription = item ? getLocalizedAI(item.ai_descriptions, effectiveLanguage) : '';

	// Available languages are whatever the AI generated for this item.
	$: availableLanguages = item?.ai_descriptions
		? Object.keys(item.ai_descriptions).filter((k) => item.ai_descriptions[k])
		: [];
	$: hasMultipleLanguages = availableLanguages.length > 1;

	function cycleLanguage() {
		if (availableLanguages.length === 0) return;
		const i = availableLanguages.indexOf(effectiveLanguage);
		contentLanguage = availableLanguages[(i + 1) % availableLanguages.length];
	}

	// Users for owner selection
	let userList: User[] = [];

	// Polling for AI processing
	let pollInterval: ReturnType<typeof setInterval> | null = null;
	let aiProcessing = false;

	$: itemId = $page.params.id;

	// Check if any images are still processing
	$: aiProcessing = item?.images.some(img => !img.ai_processed) ?? false;

	// Get suggested name from AI if item has placeholder name
	$: aiSuggestedName = getAISuggestedName();

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadItem();
		userList = await users.listUsers();

		// Start polling if AI is processing
		startPollingIfNeeded();
	});

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});

	function startPollingIfNeeded() {
		if (aiProcessing && !pollInterval) {
			pollInterval = setInterval(async () => {
				await loadItem();
				if (!aiProcessing && pollInterval) {
					clearInterval(pollInterval);
					pollInterval = null;
				}
			}, 3000); // Poll every 3 seconds
		}
	}

	$: if (aiProcessing) {
		startPollingIfNeeded();
	}

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

	function getAISuggestedName(): string | null {
		if (!item || item.name !== 'New Item') return null;

		// Use localized AI name if available
		if (localizedName) {
			return localizedName;
		}

		// Use AI tags as fallback
		const tagsImage = item.images.find(img => img.ai_processed && img.ai_tags.length > 0);
		if (tagsImage?.ai_tags.length) {
			// Use first 2-3 tags as name
			return tagsImage.ai_tags.slice(0, 3).map(t =>
				t.charAt(0).toUpperCase() + t.slice(1)
			).join(' ');
		}

		return null;
	}

	function startEdit() {
		if (!item) return;
		editData = {
			name: item.name,
			description: item.description || '',
			size: item.size || '',
			condition: item.condition,
			seasonal: item.seasonal,
			owner_id: item.owner_id || undefined,
			value_estimate: item.value_estimate || undefined
		};
		editMode = true;
	}

	function cancelEdit() {
		editMode = false;
		editData = {};
	}

	async function saveEdit() {
		if (!item) return;
		saving = true;
		try {
			// Clean up empty strings
			const updateData: ItemUpdate = {
				...editData,
				description: editData.description || undefined,
				size: editData.size || undefined,
				owner_id: editData.owner_id || undefined
			};
			await items.updateItem(item.id, updateData);
			toast.success('Item updated');
			editMode = false;
			await loadItem();
		} catch (error) {
			toast.error('Failed to update item');
		} finally {
			saving = false;
		}
	}

	async function applyAISuggestion() {
		if (!aiSuggestedName) return;
		editData.name = aiSuggestedName;

		// Also apply localized AI description if available
		if (localizedDescription) {
			editData.description = localizedDescription;
		}
	}

	async function handleDelete() {
		if (!item) return;
		if (!confirm(`Delete "${item.name}"? This cannot be undone.`)) return;

		deleting = true;
		try {
			await items.deleteItem(item.id);
			toast.success('Item deleted');
			// Navigate back to container
			if (item.path.length > 0) {
				const lastContainer = item.path[item.path.length - 1];
				goto(`/containers/${lastContainer.id}`);
			} else {
				goto('/');
			}
		} catch {
			toast.error('Failed to delete item');
		} finally {
			deleting = false;
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
			startPollingIfNeeded();
		} catch (error) {
			toast.error('Failed to upload image');
		} finally {
			uploading = false;
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

	async function setPrimaryImage(imageId: string) {
		try {
			await items.setPrimaryImage(itemId, imageId);
			toast.success('Primary image updated');
			await loadItem();
		} catch {
			toast.error('Failed to set primary image');
		}
	}

	// Sort images to put primary first, then by created_at
	$: sortedImages = item?.images.slice().sort((a, b) => {
		// Primary image first
		if (a.id === item?.primary_image_id) return -1;
		if (b.id === item?.primary_image_id) return 1;
		// Then by created_at (oldest first for other images)
		return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
	}) ?? [];

	$: conditions = (Object.keys(CONDITION_KEYS) as Condition[]).map((value) => ({
		value,
		label: $_(CONDITION_KEYS[value])
	}));

	$: seasons = (Object.keys(SEASONAL_KEYS) as Seasonal[]).map((value) => ({
		value,
		label: $_(SEASONAL_KEYS[value])
	}));
</script>

<svelte:head>
	<title>{item?.name ?? 'Item'} - StorageHub</title>
</svelte:head>

{#if loading}
	<div class="space-y-6">
		<div class="h-8 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-700"></div>
		<div class="h-64 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-700"></div>
	</div>
{:else if item}
	<div class="space-y-6">
		<!-- Breadcrumb -->
		<Breadcrumb path={item.path} currentName={item.name} />

		<!-- AI Processing Banner -->
		{#if aiProcessing}
			<div class="rounded-lg bg-primary-50 border border-primary-200 p-4 dark:bg-primary-900/20 dark:border-primary-800">
				<div class="flex items-center gap-3">
					<div class="h-5 w-5 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
					<div>
						<p class="font-medium text-primary-800 dark:text-primary-200">AI is analyzing your photos...</p>
						<p class="text-sm text-primary-600 dark:text-primary-400">This may take a few moments. The page will update automatically.</p>
					</div>
				</div>
			</div>
		{/if}

		<!-- AI Suggestion Banner -->
		{#if aiSuggestedName && item.name === 'New Item' && !editMode}
			<div class="rounded-lg bg-green-50 border border-green-200 p-4 dark:bg-green-900/20 dark:border-green-800">
				<div class="flex items-start justify-between gap-4">
					<div>
						<p class="font-medium text-green-800 dark:text-green-200">AI Suggestion Available</p>
						<p class="text-sm text-green-600 dark:text-green-400 mt-1">
							Based on your photos, we suggest naming this item: <strong>"{aiSuggestedName}"</strong>
						</p>
					</div>
					<Button size="sm" on:click={() => { startEdit(); applyAISuggestion(); }}>
						Apply & Edit
					</Button>
				</div>
			</div>
		{/if}

		<div class="grid gap-8 lg:grid-cols-2">
			<!-- Images -->
			<div>
				{#if sortedImages.length > 0}
					<div class="grid gap-4">
						{#each sortedImages as image, i}
							<div class="group relative overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
								<img
									src={image.filepath}
									alt="{item.name} - Image {i + 1}"
									class="aspect-square w-full object-cover"
								/>
								<!-- Top-right buttons -->
								<div class="absolute right-2 top-2 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
									{#if image.id !== item.primary_image_id}
										<button
											class="rounded-lg bg-primary-600 p-2 text-white"
											title="Set as primary image"
											on:click={() => setPrimaryImage(image.id)}
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
											</svg>
										</button>
									{/if}
									<button
										class="rounded-lg bg-red-600 p-2 text-white"
										title="Delete image"
										on:click={() => deleteImage(image.id)}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								</div>

								<!-- Primary badge -->
								{#if image.id === item.primary_image_id}
									<div class="absolute top-2 left-2 rounded-full bg-amber-500 px-2 py-1 text-xs font-medium text-white flex items-center gap-1">
										<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
											<path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
										</svg>
										Primary
									</div>
								{:else if !image.ai_processed}
									<!-- Processing indicator -->
									<div class="absolute top-2 left-2 rounded-full bg-primary-600 px-2 py-1 text-xs text-white flex items-center gap-1">
										<div class="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
										Processing...
									</div>
								{/if}

								<!-- AI tags overlay -->
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
							<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">No photos yet</h3>
							<p class="mt-2 text-slate-500 dark:text-slate-400">Add photos to help identify this item.</p>
						</div>
					</Card>
				{/if}

				<Button class="mt-4 w-full" variant="secondary" on:click={() => fileInput.click()} disabled={uploading}>
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
				{#if editMode}
					<!-- Edit Form -->
					<Card>
						<h3 class="mb-4 font-semibold text-slate-900 dark:text-white">Edit Item</h3>
						<form on:submit|preventDefault={saveEdit} class="space-y-4">
							<div>
								<Input
									label="Name"
									bind:value={editData.name}
									required
									id="edit-name"
								/>
								{#if aiSuggestedName && editData.name !== aiSuggestedName}
									<button
										type="button"
										class="mt-1 text-xs text-primary-600 hover:underline"
										on:click={applyAISuggestion}
									>
										Use AI suggestion: "{aiSuggestedName}"
									</button>
								{/if}
							</div>

							<div>
								<label class="label" for="edit-description">Description</label>
								<textarea
									id="edit-description"
									class="input min-h-[80px]"
									bind:value={editData.description}
									placeholder="Optional description"
								/>
							</div>

							<div class="grid gap-4 sm:grid-cols-2">
								<div>
									<label class="label" for="edit-condition">Condition</label>
									<select id="edit-condition" class="input" bind:value={editData.condition}>
										{#each conditions as cond}
											<option value={cond.value}>{cond.label}</option>
										{/each}
									</select>
								</div>

								<div>
									<label class="label" for="edit-seasonal">Season</label>
									<select id="edit-seasonal" class="input" bind:value={editData.seasonal}>
										{#each seasons as season}
											<option value={season.value}>{season.label}</option>
										{/each}
									</select>
								</div>
							</div>

							<div class="grid gap-4 sm:grid-cols-2">
								<Input
									label="Size"
									bind:value={editData.size}
									placeholder="e.g., Small, Medium, Large"
									id="edit-size"
								/>

								<div>
									<label class="label" for="edit-value">Estimated Value</label>
									<input
										type="number"
										id="edit-value"
										class="input"
										bind:value={editData.value_estimate}
										placeholder="0.00"
										step="0.01"
										min="0"
									/>
								</div>
							</div>

							<div>
								<label class="label" for="edit-owner">Owner</label>
								<select id="edit-owner" class="input" bind:value={editData.owner_id}>
									<option value={undefined}>No owner</option>
									{#each userList as u}
										<option value={u.id}>{u.name}</option>
									{/each}
								</select>
							</div>

							<div class="flex gap-2 pt-2">
								<Button variant="secondary" type="button" on:click={cancelEdit}>Cancel</Button>
								<Button type="submit" loading={saving} class="flex-1">Save Changes</Button>
							</div>
						</form>
					</Card>
				{:else}
					<!-- View Mode -->
					<div>
						<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{item.name}</h1>
						{#if item.description || localizedDescription}
							<div class="mt-2">
								<p class="text-slate-600 dark:text-slate-400">{item.description || localizedDescription}</p>
								{#if hasMultipleLanguages && !item.description}
									<button
										class="mt-1 inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400"
										on:click={cycleLanguage}
										title={availableLanguages.join(' / ')}
									>
										<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
										</svg>
										{effectiveLanguage.toUpperCase()} → {availableLanguages[(availableLanguages.indexOf(effectiveLanguage) + 1) % availableLanguages.length].toUpperCase()}
									</button>
								{/if}
							</div>
						{/if}
					</div>

					<Card>
						<h3 class="mb-4 font-semibold text-slate-900 dark:text-white">Details</h3>
						<dl class="space-y-3">
							{#if item.owner}
								<div class="flex justify-between">
									<dt class="text-slate-500 dark:text-slate-400">Owner</dt>
									<dd class="font-medium text-slate-900 dark:text-white">{item.owner.name}</dd>
								</div>
							{/if}
							<div class="flex justify-between">
								<dt class="text-slate-500 dark:text-slate-400">Condition</dt>
								<dd>
									<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
										{item.condition === 'good' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
										 item.condition === 'fair' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
										 item.condition === 'damaged' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
										 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'}">
										{$_(CONDITION_KEYS[item.condition])}
									</span>
								</dd>
							</div>
							{#if item.size}
								<div class="flex justify-between">
									<dt class="text-slate-500 dark:text-slate-400">Size</dt>
									<dd class="font-medium text-slate-900 dark:text-white">{item.size}</dd>
								</div>
							{/if}
							{#if item.seasonal !== 'none'}
								<div class="flex justify-between">
									<dt class="text-slate-500 dark:text-slate-400">Season</dt>
									<dd>
										<span class="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
											{$_(SEASONAL_KEYS[item.seasonal])}
										</span>
									</dd>
								</div>
							{/if}
							{#if item.value_estimate}
								<div class="flex justify-between">
									<dt class="text-slate-500 dark:text-slate-400">Est. Value</dt>
									<dd class="font-medium text-slate-900 dark:text-white">${item.value_estimate}</dd>
								</div>
							{/if}
						</dl>
					</Card>

					{#if item.tags.length > 0}
						<Card>
							<h3 class="mb-4 font-semibold text-slate-900 dark:text-white">Tags</h3>
							<div class="flex flex-wrap gap-2">
								{#each item.tags as tag}
									<span class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700 dark:bg-slate-700 dark:text-slate-300">
										{tag.name}
									</span>
								{/each}
							</div>
						</Card>
					{/if}

					<div class="flex gap-2">
						<Button variant="secondary" class="flex-1" on:click={startEdit}>Edit</Button>
						<Button variant="danger" on:click={handleDelete} loading={deleting}>Delete</Button>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
