<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { containers, items } from '$lib/api';
	import { ItemCard, ContainerCard, Breadcrumb, Button, Card, Input, Modal, ShareModal } from '$lib/components';
	import { PrintModal } from '$lib/components/print';
	import { _ } from '$lib/i18n';
	import { CONTAINER_TYPES, CONTAINER_TYPE_KEYS } from '$lib/utils/itemEnums';
	import type { ContainerWithItems, ContainerUpdate, ItemCreate, PrintResult } from '$lib/types';

	let container: ContainerWithItems | null = null;
	let loading = true;
	let showCreateModal = false;
	let showPrintModal = false;
	let showShareModal = false;
	let showEditModal = false;
	let creating = false;
	let savingEdit = false;
	let uploadingImage = false;

	let newItem: ItemCreate = {
		name: '',
		description: '',
		container_id: ''
	};

	let editData: ContainerUpdate = {};
	let imageFileInput: HTMLInputElement;

	$: containerId = $page.params.id!;

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadContainer();
	});

	async function loadContainer() {
		loading = true;
		try {
			container = await containers.getContainer(containerId);
			newItem.container_id = container.id;
		} catch {
			toast.error('Container not found');
			goto('/');
		} finally {
			loading = false;
		}
	}

	async function handleCreateItem() {
		if (!newItem.name.trim()) return;

		creating = true;
		try {
			const created = await items.createItem(newItem);
			toast.success('Item created successfully');
			showCreateModal = false;
			newItem = { name: '', description: '', container_id: containerId };
			goto(`/items/${created.id}`);
		} catch (error) {
			toast.error('Failed to create item');
		} finally {
			creating = false;
		}
	}

	function handlePrinted(event: CustomEvent<PrintResult>) {
		const result = event.detail;
		if (result.success) {
			toast.success(result.message || 'Label sent to printer');
		}
	}

	function openEditModal() {
		if (!container) return;
		editData = {
			name: container.name,
			notes: container.notes ?? undefined,
			container_type: container.container_type
		};
		showEditModal = true;
	}

	async function handleSaveEdit() {
		if (!container) return;
		savingEdit = true;
		try {
			await containers.updateContainer(container.id, editData);
			toast.success('Container updated');
			showEditModal = false;
			await loadContainer();
		} catch {
			toast.error('Failed to update container');
		} finally {
			savingEdit = false;
		}
	}

	async function handleImagePick(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file || !container) return;
		uploadingImage = true;
		try {
			await containers.uploadContainerImage(container.id, file);
			toast.success('Image updated');
			await loadContainer();
		} catch {
			toast.error('Failed to upload image');
		} finally {
			uploadingImage = false;
			// Reset so picking the same file again still triggers `change`.
			target.value = '';
		}
	}

	async function handleRemoveImage() {
		if (!container) return;
		if (!confirm($_('containers.removeImage') + '?')) return;
		uploadingImage = true;
		try {
			await containers.deleteContainerImage(container.id);
			toast.success('Image removed');
			await loadContainer();
		} catch {
			toast.error('Failed to remove image');
		} finally {
			uploadingImage = false;
		}
	}
</script>

<svelte:head>
	<title>{container?.name ?? 'Container'} - StorageHub</title>
</svelte:head>

{#if loading}
	<div class="space-y-6">
		<div class="h-8 w-48 animate-pulse rounded bg-slate-200"></div>
		<div class="h-12 w-64 animate-pulse rounded bg-slate-200"></div>
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
			{#each [1, 2, 3, 4] as _}
				<div class="aspect-square animate-pulse rounded-xl bg-slate-200"></div>
			{/each}
		</div>
	</div>
{:else if container}
	<div class="space-y-6">
		<!-- Breadcrumb -->
		<Breadcrumb path={container.path} currentName={container.name} />

		<!-- Header -->
		<div class="flex items-start justify-between">
			<div class="flex-1">
				<h1 class="text-2xl font-bold text-slate-900">{container.name}</h1>
				{#if container.container_type}
					<span class="mt-1 inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
						{$_(CONTAINER_TYPE_KEYS[container.container_type])}
					</span>
				{/if}
				{#if container.notes}
					<p class="mt-1 text-slate-500">{container.notes}</p>
				{/if}
			</div>
			<div class="flex gap-2">
				<Button variant="secondary" on:click={openEditModal}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
					</svg>
					{$_('common.edit')}
				</Button>
				<Button variant="secondary" on:click={() => (showShareModal = true)}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
					</svg>
					Share
				</Button>
				<Button variant="secondary" on:click={() => (showPrintModal = true)}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
					</svg>
					Print Label
				</Button>
				<Button on:click={() => (showCreateModal = true)}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add Item
				</Button>
			</div>
		</div>

		<!-- Hero Image -->
		<input
			bind:this={imageFileInput}
			type="file"
			accept="image/*"
			class="hidden"
			on:change={handleImagePick}
		/>
		{#if container.image_url}
			<Card padding="none">
				<div class="relative">
					<img
						src={container.image_url}
						alt={container.name}
						class="aspect-[3/2] w-full rounded-xl object-cover"
					/>
					<div class="absolute right-3 top-3 flex gap-2">
						<Button variant="secondary" loading={uploadingImage} on:click={() => imageFileInput.click()}>
							{$_('containers.replaceImage')}
						</Button>
						<Button variant="danger" loading={uploadingImage} on:click={handleRemoveImage}>
							{$_('containers.removeImage')}
						</Button>
					</div>
				</div>
			</Card>
		{:else}
			<Card>
				<div class="flex items-center justify-between">
					<p class="text-sm text-slate-500 dark:text-slate-400">{$_('containers.image')}</p>
					<Button variant="secondary" loading={uploadingImage} on:click={() => imageFileInput.click()}>
						{$_('containers.chooseImage')}
					</Button>
				</div>
			</Card>
		{/if}

		<!-- QR Code -->
		<Card>
			<div class="flex items-center gap-6">
				<img
					src={containers.getContainerQRUrl(container.id)}
					alt="QR Code"
					class="h-24 w-24 rounded-lg border border-slate-200"
				/>
				<div>
					<p class="text-sm font-medium text-slate-500">{$_('containers.quickAccessCode')}</p>
					<p class="mt-1 font-mono text-lg text-slate-900">{container.qr_code}</p>
					<p class="mt-2 text-sm text-slate-500">{$_('containers.quickAccessHelp')}</p>
				</div>
			</div>
		</Card>

		<!-- Child Containers -->
		{#if container.child_containers.length > 0}
			<div>
				<h2 class="mb-4 text-lg font-semibold text-slate-900">{$_('containers.nestedContainers')}</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each container.child_containers as child}
						<ContainerCard container={child} />
					{/each}
				</div>
			</div>
		{/if}

		<!-- Items -->
		<div>
			<h2 class="mb-4 text-lg font-semibold text-slate-900">{$_('items.title')} ({container.items.length})</h2>
			{#if container.items.length === 0}
				<Card>
					<div class="py-12 text-center">
						<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
						</svg>
						<h3 class="mt-4 text-lg font-medium text-slate-900">{$_('containers.noItems')}</h3>
						<p class="mt-2 text-slate-500">{$_('containers.addItemsHelp')}</p>
						<Button class="mt-4" on:click={() => (showCreateModal = true)}>{$_('items.addItem')}</Button>
					</div>
				</Card>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
					{#each container.items as item}
						<ItemCard {item} />
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- Create Item Modal -->
<Modal open={showCreateModal} title={$_('items.addItem')} on:close={() => (showCreateModal = false)}>
	<form on:submit|preventDefault={handleCreateItem} class="space-y-4">
		<Input
			label={$_('common.name')}
			placeholder={$_('containers.namePlaceholder')}
			bind:value={newItem.name}
			required
			id="item-name"
		/>
		<Input
			label={$_('common.description')}
			placeholder={$_('locations.descriptionPlaceholder')}
			bind:value={newItem.description}
			id="item-description"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showCreateModal = false)}>{$_('common.cancel')}</Button>
		<Button loading={creating} on:click={handleCreateItem}>{$_('common.create')}</Button>
	</svelte:fragment>
</Modal>

<!-- Print Label Modal -->
{#if container}
	<PrintModal
		open={showPrintModal}
		containerId={container.id}
		containerName={container.name}
		on:close={() => (showPrintModal = false)}
		on:printed={handlePrinted}
	/>
{/if}

<!-- Share Modal -->
{#if showShareModal && container}
	<ShareModal
		containerId={container.id}
		containerName={container.name}
		on:close={() => (showShareModal = false)}
	/>
{/if}

<!-- Edit Container Modal -->
{#if container}
	<Modal open={showEditModal} title={$_('containers.editContainer')} on:close={() => (showEditModal = false)}>
		<form on:submit|preventDefault={handleSaveEdit} class="space-y-4">
			<Input
				label={$_('common.name')}
				bind:value={editData.name}
				required
				id="edit-container-name"
			/>

			<div>
				<label for="edit-container-type" class="label">{$_('containers.containerType')}</label>
				<select
					id="edit-container-type"
					class="input"
					bind:value={editData.container_type}
				>
					<option value={null}>{$_('containers.chooseType')}</option>
					{#each CONTAINER_TYPES as t}
						<option value={t}>{$_(CONTAINER_TYPE_KEYS[t])}</option>
					{/each}
				</select>
			</div>

			<Input
				label={$_('items.notes')}
				bind:value={editData.notes}
				id="edit-container-notes"
			/>
		</form>

		<svelte:fragment slot="footer">
			<Button variant="secondary" on:click={() => (showEditModal = false)}>{$_('common.cancel')}</Button>
			<Button loading={savingEdit} on:click={handleSaveEdit}>{$_('common.save')}</Button>
		</svelte:fragment>
	</Modal>
{/if}
