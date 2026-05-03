<script lang="ts">
	import { createEventDispatcher, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from '$lib/stores/toast';
	import { locations, containers, items } from '$lib/api';
	import { Button, Input, Modal, Card, CameraCapture, SinglePhotoCapture } from '$lib/components';
	import { _, locale } from '$lib/i18n';
	import { getLocalizedAI } from '$lib/utils/localized';
	import { CONTAINER_TYPES, CONTAINER_TYPE_KEYS } from '$lib/utils/itemEnums';
	import type { Location, Container, ContainerCreate, LocationCreate, Item } from '$lib/types';

	export let open = false;

	const dispatch = createEventDispatcher<{ close: void }>();

	type Step = 'select-location' | 'create-location' | 'select-container' | 'create-container' | 'camera' | 'batch-review' | 'saving' | 'done';

	let step: Step = 'select-location';
	let loading = false;
	let saving = false;

	// Data
	let locationList: Location[] = [];
	let containerList: Container[] = [];

	// Selections
	let selectedLocation: Location | null = null;
	let selectedContainer: Container | null = null;

	// New location form
	let newLocation: LocationCreate = {
		name: '',
		description: ''
	};

	// New container form
	let newContainer: ContainerCreate = {
		name: '',
		location_id: '',
		notes: '',
		container_type: null
	};
	let newContainerImage: File | null = null;

	// Batch items - each item has its own photos
	let batchItems: { photos: File[]; previews: string[] }[] = [];

	// Created items (after save)
	let createdItems: { item: Item; aiProcessing: boolean; aiNames: Record<string, string> }[] = [];

	// Overall progress
	let savingProgress = 0;
	let totalToSave = 0;

	// Polling for AI processing
	let pollInterval: ReturnType<typeof setInterval> | null = null;

	$: if (open && step === 'select-location') {
		loadLocations();
	}

	onDestroy(() => {
		if (pollInterval) clearInterval(pollInterval);
		cleanupPreviews();
	});

	function cleanupPreviews() {
		batchItems.forEach((item) => item.previews.forEach((p) => URL.revokeObjectURL(p)));
	}

	async function loadLocations() {
		loading = true;
		try {
			locationList = await locations.listLocations();
		} catch (error) {
			toast.error('Failed to load locations');
		} finally {
			loading = false;
		}
	}

	async function selectLocation(location: Location) {
		selectedLocation = location;
		loading = true;
		try {
			containerList = await containers.listContainers(location.id);
			step = 'select-container';
		} catch (error) {
			toast.error('Failed to load containers');
		} finally {
			loading = false;
		}
	}

	function startCreateLocation() {
		step = 'create-location';
	}

	async function handleCreateLocation() {
		if (!newLocation.name.trim()) return;

		saving = true;
		try {
			const created = await locations.createLocation(newLocation);
			toast.success('Location created');
			selectedLocation = created;
			newLocation = { name: '', description: '' };
			// Load containers (will be empty for new location)
			containerList = [];
			step = 'select-container';
		} catch (error) {
			toast.error('Failed to create location');
		} finally {
			saving = false;
		}
	}

	function selectContainer(container: Container) {
		selectedContainer = container;
		step = 'camera';
	}

	function startCreateContainer() {
		if (selectedLocation) {
			newContainer.location_id = selectedLocation.id;
			step = 'create-container';
		}
	}

	async function handleCreateContainer() {
		if (!newContainer.name.trim()) return;

		saving = true;
		try {
			const created = await containers.createContainer(newContainer);
			if (newContainerImage) {
				try {
					await containers.uploadContainerImage(created.id, newContainerImage);
				} catch {
					toast.error('Container created, but image upload failed');
				}
			}
			toast.success('Container created');
			selectedContainer = created;
			newContainer = { name: '', location_id: '', notes: '', container_type: null };
			newContainerImage = null;
			step = 'camera';
		} catch (error) {
			toast.error('Failed to create container');
		} finally {
			saving = false;
		}
	}


	function handleBatch(event: CustomEvent<{ items: File[][] }>) {
		const batchPhotos = event.detail.items;

		// Convert to our batch format with previews
		batchItems = batchPhotos.map((photos) => ({
			photos,
			previews: photos.map((f) => URL.createObjectURL(f))
		}));

		// Go to batch review screen
		step = 'batch-review';
	}

	function handleCameraCancel() {
		if (batchItems.length > 0) {
			// Go back to review if we have items
			step = 'batch-review';
		} else {
			// Otherwise go back to container selection
			step = 'select-container';
		}
	}

	function handleCameraError(event: CustomEvent<{ message: string }>) {
		toast.error(event.detail.message);
	}

	function addMoreItems() {
		step = 'camera';
	}

	function removeItem(index: number) {
		// Cleanup previews for this item
		batchItems[index].previews.forEach((p) => URL.revokeObjectURL(p));
		batchItems = batchItems.filter((_, i) => i !== index);

		if (batchItems.length === 0) {
			step = 'camera';
		}
	}

	async function saveAllItems() {
		if (!selectedContainer || batchItems.length === 0) return;

		step = 'saving';
		saving = true;
		totalToSave = batchItems.length;
		savingProgress = 0;
		createdItems = [];

		try {
			// Create all items
			for (let i = 0; i < batchItems.length; i++) {
				const batchItem = batchItems[i];
				savingProgress = i + 1;

				// Create item
				const item = await items.createItem({
					name: 'New Item',
					description: '',
					container_id: selectedContainer.id
				});

				// Upload all photos for this item
				for (const photo of batchItem.photos) {
					try {
						await items.uploadItemImage(item.id, photo);
					} catch (uploadError) {
						console.error('Failed to upload photo:', uploadError);
					}
				}

				createdItems = [...createdItems, { item, aiProcessing: true, aiNames: {} }];
			}

			toast.success(`${batchItems.length} item${batchItems.length > 1 ? 's' : ''} created! AI is analyzing...`);
			step = 'done';

			// Start polling for AI results
			startAIPolling();
		} catch (error) {
			toast.error('Failed to create items');
			step = 'batch-review';
		} finally {
			saving = false;
		}
	}

	function startAIPolling() {
		pollInterval = setInterval(async () => {
			if (createdItems.length === 0) return;

			let allProcessed = true;
			const updatedItems = [...createdItems];

			for (let i = 0; i < updatedItems.length; i++) {
				if (updatedItems[i].aiProcessing) {
					try {
						const itemDetails = await items.getItem(updatedItems[i].item.id);
						updatedItems[i].item = itemDetails;

						if (itemDetails.ai_processed) {
							updatedItems[i].aiProcessing = false;
							updatedItems[i].aiNames = itemDetails.ai_names || {};
						} else {
							allProcessed = false;
						}
					} catch (error) {
						console.error('Failed to fetch item:', error);
						allProcessed = false;
					}
				}
			}

			createdItems = updatedItems;

			if (allProcessed && pollInterval) {
				clearInterval(pollInterval);
				pollInterval = null;
			}
		}, 3000);
	}

	async function updateItemName(index: number, name: string) {
		if (!createdItems[index]) return;

		try {
			await items.updateItem(createdItems[index].item.id, { name });
			createdItems[index].item.name = name;
			createdItems = [...createdItems];
		} catch (error) {
			toast.error('Failed to update item');
		}
	}

	function applyAIName(index: number) {
		const nameToApply = getLocalizedAI(createdItems[index].aiNames);
		if (nameToApply) {
			updateItemName(index, nameToApply);
		}
	}

	function getLocalizedAIName(index: number): string {
		return getLocalizedAI(createdItems[index].aiNames);
	}

	function handleDone() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}

		// Navigate to container
		if (selectedContainer) {
			goto(`/containers/${selectedContainer.id}`);
		}

		handleClose();
	}

	function goBack() {
		if (step === 'select-container') {
			selectedLocation = null;
			step = 'select-location';
		} else if (step === 'create-location') {
			step = 'select-location';
		} else if (step === 'create-container') {
			step = 'select-container';
		} else if (step === 'batch-review' && createdItems.length === 0) {
			// Only allow going back if items haven't been created yet
			cleanupPreviews();
			batchItems = [];
			step = 'camera';
		}
	}

	function handleClose() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
		open = false;
		step = 'select-location';
		cleanupPreviews();
		batchItems = [];
		createdItems = [];
		savingProgress = 0;
		totalToSave = 0;
		selectedLocation = null;
		selectedContainer = null;
		newLocation = { name: '', description: '' };
		newContainer = { name: '', location_id: '', notes: '' };
		dispatch('close');
	}

	// Check how many items are still being processed by AI
	$: aiProcessingCount = createdItems.filter((i) => i.aiProcessing).length;
</script>

{#if open}
	{#if step === 'camera'}
		<!-- Full screen camera with batch mode -->
		<div class="fixed inset-0 z-50 bg-black">
			<CameraCapture
				active={true}
				batchMode={true}
				maxPhotosPerItem={10}
				on:batch={handleBatch}
				on:cancel={handleCameraCancel}
				on:error={handleCameraError}
			/>
		</div>
	{:else if step === 'batch-review' || step === 'saving' || step === 'done'}
		<!-- Full screen batch review -->
		<div class="fixed inset-0 z-50 flex flex-col bg-slate-50 dark:bg-slate-900">
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
				<div>
					<h2 class="font-semibold text-slate-900 dark:text-white">
						{#if step === 'done'}
							Items Created
						{:else if step === 'saving'}
							Creating Items...
						{:else}
							Review Items
						{/if}
					</h2>
					<p class="text-sm text-slate-500 dark:text-slate-400">
						{selectedLocation?.name} → {selectedContainer?.name}
					</p>
				</div>
				{#if step === 'batch-review'}
					<button class="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300" on:click={handleClose}>
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				{/if}
			</div>

			<!-- AI Processing Banner -->
			{#if aiProcessingCount > 0}
				<div class="bg-primary-50 border-b border-primary-200 px-4 py-3 dark:bg-primary-900/20 dark:border-primary-800">
					<div class="flex items-center gap-3">
						<div class="h-5 w-5 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
						<p class="text-sm text-primary-700 dark:text-primary-300">
							AI is analyzing {aiProcessingCount} item{aiProcessingCount > 1 ? 's' : ''}...
						</p>
					</div>
				</div>
			{/if}

			<!-- Items list -->
			<div class="flex-1 overflow-y-auto p-4 pb-24">
				{#if step === 'done'}
					<!-- Post-save: show created items with AI suggestions -->
					<div class="space-y-3">
						{#each createdItems as createdItem, index}
							<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
								<div class="flex gap-4">
									<div class="flex-shrink-0">
										{#if batchItems[index]?.previews[0]}
											<img src={batchItems[index].previews[0]} alt="Item {index + 1}" class="h-16 w-16 rounded-lg object-cover" />
										{:else}
											<div class="h-16 w-16 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
												<svg class="h-6 w-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
												</svg>
											</div>
										{/if}
									</div>
									<div class="flex-1 min-w-0">
										<input
											type="text"
											class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-white"
											value={createdItem.item.name}
											on:blur={(e) => updateItemName(index, e.currentTarget.value)}
										/>
										{#if getLocalizedAIName(index) && createdItem.item.name !== getLocalizedAIName(index)}
											<button
												class="mt-1 text-xs text-primary-600 hover:underline dark:text-primary-400"
												on:click={() => applyAIName(index)}
											>
												AI suggests: "{getLocalizedAIName(index)}"
											</button>
										{:else if createdItem.aiProcessing}
											<div class="mt-1 flex items-center gap-2">
												<div class="h-3 w-3 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
												<p class="text-xs text-slate-400">Analyzing...</p>
											</div>
										{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<!-- Pre-save: show batch items -->
					<div class="space-y-4">
						{#each batchItems as batchItem, itemIndex}
							<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
								<div class="flex items-start justify-between mb-3">
									<span class="text-sm font-medium text-slate-700 dark:text-slate-300">
										Item {itemIndex + 1}
									</span>
									<button
										class="text-red-500 hover:text-red-700 text-sm"
										on:click={() => removeItem(itemIndex)}
									>
										Remove
									</button>
								</div>
								<div class="flex gap-2 overflow-x-auto pb-1">
									{#each batchItem.previews as preview, photoIndex}
										<img
											src={preview}
											alt="Item {itemIndex + 1}, Photo {photoIndex + 1}"
											class="h-16 w-16 flex-shrink-0 rounded-lg object-cover"
										/>
									{/each}
								</div>
								<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
									{batchItem.photos.length} photo{batchItem.photos.length > 1 ? 's' : ''}
								</p>
							</div>
						{/each}

						<p class="text-sm text-slate-500 dark:text-slate-400 text-center">
							{batchItems.length} item{batchItems.length > 1 ? 's' : ''} ready to save. AI will analyze and suggest names.
						</p>
					</div>
				{/if}
			</div>

			<!-- Footer actions -->
			<div class="fixed bottom-0 left-0 right-0 border-t border-slate-200 bg-white p-4 pb-safe dark:border-slate-700 dark:bg-slate-800">
				{#if step === 'done'}
					<Button class="w-full" on:click={handleDone}>
						Done
					</Button>
				{:else if step === 'saving'}
					<div class="flex flex-col items-center gap-2 py-2">
						<div class="h-5 w-5 animate-spin rounded-full border-2 border-primary-600 border-t-transparent"></div>
						<span class="text-slate-600 dark:text-slate-300">
							Creating item {savingProgress} of {totalToSave}...
						</span>
					</div>
				{:else}
					<div class="flex gap-3">
						<Button variant="secondary" on:click={addMoreItems}>
							<svg class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							Add More
						</Button>
						<Button class="flex-1" on:click={saveAllItems}>
							Save {batchItems.length} Item{batchItems.length > 1 ? 's' : ''}
						</Button>
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<!-- Modal for location/container selection -->
		<Modal
			open={true}
			title={step === 'select-location' ? 'Select Location' : step === 'create-location' ? 'New Location' : step === 'select-container' ? 'Select Container' : 'New Container'}
			on:close={handleClose}
		>
			{#if loading}
				<div class="flex items-center justify-center py-12">
					<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
				</div>
			{:else if step === 'select-location'}
				<!-- Location selection -->
				<div class="space-y-2">
					<p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Where are these items stored?</p>

					<!-- Create new location option -->
					<button
						class="w-full rounded-lg border-2 border-dashed border-slate-300 p-4 text-left transition hover:border-primary-400 hover:bg-primary-50 dark:border-slate-600 dark:hover:border-primary-500 dark:hover:bg-primary-900/20"
						on:click={startCreateLocation}
					>
						<div class="flex items-center gap-3">
							<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
								</svg>
							</div>
							<div>
								<p class="font-medium text-slate-700 dark:text-slate-300">New location</p>
								<p class="text-sm text-slate-500 dark:text-slate-400">Create a new storage location</p>
							</div>
						</div>
					</button>

					{#if locationList.length === 0}
						<div class="py-4 text-center text-slate-500 dark:text-slate-400">
							<p>No locations yet</p>
						</div>
					{:else}
						{#each locationList as location}
							<button
								class="w-full rounded-lg border border-slate-200 p-4 text-left transition hover:border-primary-300 hover:bg-primary-50 dark:border-slate-700 dark:hover:border-primary-600 dark:hover:bg-primary-900/20"
								on:click={() => selectLocation(location)}
							>
								<div class="flex items-center gap-3">
									<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-400">
										<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
										</svg>
									</div>
									<div>
										<p class="font-medium text-slate-900 dark:text-white">{location.name}</p>
										{#if location.description}
											<p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-1">{location.description}</p>
										{/if}
									</div>
								</div>
							</button>
						{/each}
					{/if}
				</div>
			{:else if step === 'create-location'}
				<!-- Create location form -->
				<div class="space-y-4">
					<button
						class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
						on:click={goBack}
					>
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
						</svg>
						Back to locations
					</button>

					<Input
						label="Location name"
						placeholder="e.g., Garage, Attic, Storage Unit"
						bind:value={newLocation.name}
						required
						id="location-name"
					/>
					<Input
						label="Description"
						placeholder="Optional description"
						bind:value={newLocation.description}
						id="location-description"
					/>
				</div>
			{:else if step === 'select-container'}
				<!-- Container selection -->
				<div class="space-y-2">
					<button
						class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 mb-4"
						on:click={goBack}
					>
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
						</svg>
						{selectedLocation?.name}
					</button>

					<!-- Create new container option -->
					<button
						class="w-full rounded-lg border-2 border-dashed border-slate-300 p-4 text-left transition hover:border-primary-400 hover:bg-primary-50 dark:border-slate-600 dark:hover:border-primary-500 dark:hover:bg-primary-900/20"
						on:click={startCreateContainer}
					>
						<div class="flex items-center gap-3">
							<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
								</svg>
							</div>
							<div>
								<p class="font-medium text-slate-700 dark:text-slate-300">New container</p>
								<p class="text-sm text-slate-500 dark:text-slate-400">Create a new container here</p>
							</div>
						</div>
					</button>

					{#if containerList.length === 0}
						<div class="py-4 text-center text-slate-500 dark:text-slate-400">
							<p>No containers in this location</p>
						</div>
					{:else}
						{#each containerList as container}
							<button
								class="w-full rounded-lg border border-slate-200 p-4 text-left transition hover:border-primary-300 hover:bg-primary-50 dark:border-slate-700 dark:hover:border-primary-600 dark:hover:bg-primary-900/20"
								on:click={() => selectContainer(container)}
							>
								<div class="flex items-center gap-3">
									<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-400">
										<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
										</svg>
									</div>
									<div>
										<p class="font-medium text-slate-900 dark:text-white">{container.name}</p>
										{#if container.notes}
											<p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-1">{container.notes}</p>
										{/if}
									</div>
								</div>
							</button>
						{/each}
					{/if}
				</div>
			{:else if step === 'create-container'}
				<!-- Create container form -->
				<div class="space-y-4">
					<button
						class="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
						on:click={goBack}
					>
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
						</svg>
						Back to containers
					</button>

					<Input
						label={$_('containers.containerName')}
						placeholder={$_('containers.containerNamePlaceholder')}
						bind:value={newContainer.name}
						required
						id="container-name"
					/>

					<div>
						<label for="qa-container-type" class="label">{$_('containers.containerType')}</label>
						<select
							id="qa-container-type"
							class="input"
							bind:value={newContainer.container_type}
						>
							<option value={null}>{$_('containers.chooseType')}</option>
							{#each CONTAINER_TYPES as t}
								<option value={t}>{$_(CONTAINER_TYPE_KEYS[t])}</option>
							{/each}
						</select>
					</div>

					<Input
						label={$_('items.notes')}
						placeholder={$_('containers.notesPlaceholder')}
						bind:value={newContainer.notes}
						id="container-notes"
					/>

					<div>
						<label class="label">{$_('containers.image')}</label>
						<SinglePhotoCapture bind:value={newContainerImage} />
					</div>
				</div>
			{/if}

			<svelte:fragment slot="footer">
				{#if step === 'create-location'}
					<Button variant="secondary" on:click={goBack}>Cancel</Button>
					<Button loading={saving} on:click={handleCreateLocation} disabled={!newLocation.name.trim()}>
						Create Location
					</Button>
				{:else if step === 'create-container'}
					<Button variant="secondary" on:click={goBack}>Cancel</Button>
					<Button loading={saving} on:click={handleCreateContainer} disabled={!newContainer.name.trim()}>
						Create Container
					</Button>
				{:else}
					<Button variant="secondary" on:click={handleClose}>Cancel</Button>
				{/if}
			</svelte:fragment>
		</Modal>
	{/if}
{/if}
