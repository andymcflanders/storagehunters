<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { containers, items } from '$lib/api';
	import * as printers from '$lib/api/printers';
	import { ItemCard, ContainerCard, Breadcrumb, Button, Card, Input, Modal } from '$lib/components';
	import type { ContainerWithItems, ItemCreate, Printer } from '$lib/types';

	let container: ContainerWithItems | null = null;
	let loading = true;
	let showCreateModal = false;
	let showPrintModal = false;
	let creating = false;
	let printing = false;

	let printerList: Printer[] = [];
	let selectedPrinterId = '';
	let previewUrl = '';

	let newItem: ItemCreate = {
		name: '',
		description: '',
		container_id: ''
	};

	$: containerId = $page.params.id;

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

	async function openPrintModal() {
		showPrintModal = true;
		try {
			printerList = await printers.getPrinters();
			// Select default printer if available
			const defaultPrinter = printerList.find((p) => p.is_default);
			selectedPrinterId = defaultPrinter?.id ?? printerList[0]?.id ?? '';
			updatePreview();
		} catch (error) {
			toast.error('Failed to load printers');
		}
	}

	function updatePreview() {
		if (selectedPrinterId && containerId) {
			previewUrl = printers.getPreviewUrl(selectedPrinterId, containerId);
		}
	}

	async function handlePrint() {
		if (!selectedPrinterId) {
			toast.warning('Please select a printer');
			return;
		}

		printing = true;
		try {
			const result = await printers.printLabel(selectedPrinterId, containerId);
			if (result.success) {
				toast.success(result.message || 'Label sent to printer');
				showPrintModal = false;
			} else {
				toast.error(result.message || 'Print failed');
			}
		} catch (error) {
			toast.error('Failed to print label');
		} finally {
			printing = false;
		}
	}

	function downloadPdf() {
		if (selectedPrinterId && containerId) {
			window.open(printers.getPreviewUrl(selectedPrinterId, containerId), '_blank');
		}
	}

	$: if (selectedPrinterId) updatePreview();
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
				{#if container.notes}
					<p class="mt-1 text-slate-500">{container.notes}</p>
				{/if}
			</div>
			<div class="flex gap-2">
				<Button variant="secondary" on:click={openPrintModal}>
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

		<!-- QR Code -->
		<Card>
			<div class="flex items-center gap-6">
				<img
					src={containers.getContainerQRUrl(container.id)}
					alt="QR Code"
					class="h-24 w-24 rounded-lg border border-slate-200"
				/>
				<div>
					<p class="text-sm font-medium text-slate-500">Quick access code</p>
					<p class="mt-1 font-mono text-lg text-slate-900">{container.qr_code}</p>
					<p class="mt-2 text-sm text-slate-500">Scan this code to quickly find this container</p>
				</div>
			</div>
		</Card>

		<!-- Child Containers -->
		{#if container.child_containers.length > 0}
			<div>
				<h2 class="mb-4 text-lg font-semibold text-slate-900">Nested Containers</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each container.child_containers as child}
						<ContainerCard container={child} />
					{/each}
				</div>
			</div>
		{/if}

		<!-- Items -->
		<div>
			<h2 class="mb-4 text-lg font-semibold text-slate-900">Items ({container.items.length})</h2>
			{#if container.items.length === 0}
				<Card>
					<div class="py-12 text-center">
						<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
						</svg>
						<h3 class="mt-4 text-lg font-medium text-slate-900">No items yet</h3>
						<p class="mt-2 text-slate-500">Add items to this container to keep track of your belongings.</p>
						<Button class="mt-4" on:click={() => (showCreateModal = true)}>Add Item</Button>
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
<Modal open={showCreateModal} title="Add Item" on:close={() => (showCreateModal = false)}>
	<form on:submit|preventDefault={handleCreateItem} class="space-y-4">
		<Input
			label="Name"
			placeholder="e.g., Winter jacket, Christmas decorations"
			bind:value={newItem.name}
			required
			id="item-name"
		/>
		<Input
			label="Description"
			placeholder="Optional description"
			bind:value={newItem.description}
			id="item-description"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showCreateModal = false)}>Cancel</Button>
		<Button loading={creating} on:click={handleCreateItem}>Create Item</Button>
	</svelte:fragment>
</Modal>

<!-- Print Label Modal -->
<Modal open={showPrintModal} title="Print Label" on:close={() => (showPrintModal = false)}>
	<div class="space-y-4">
		{#if printerList.length === 0}
			<div class="rounded-lg bg-amber-50 p-4 text-center">
				<svg class="mx-auto h-8 w-8 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
					/>
				</svg>
				<p class="mt-2 text-amber-700">No printers configured</p>
				<a href="/printers" class="mt-2 inline-block text-sm text-primary-600 hover:underline">
					Add a printer
				</a>
			</div>
		{:else}
			<div>
				<label for="printer-select" class="mb-1.5 block text-sm font-medium text-slate-700">Select Printer</label>
				<select
					id="printer-select"
					bind:value={selectedPrinterId}
					class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				>
					{#each printerList as printer}
						<option value={printer.id}>
							{printer.name}
							{#if printer.is_default}(Default){/if}
						</option>
					{/each}
				</select>
			</div>

			{#if previewUrl}
				<div>
					<p class="mb-2 text-sm font-medium text-slate-700">Preview</p>
					<div class="overflow-hidden rounded-lg border border-slate-200 bg-slate-50 p-4">
						<img
							src={previewUrl}
							alt="Label preview"
							class="mx-auto max-h-48 object-contain"
							on:error={() => (previewUrl = '')}
						/>
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showPrintModal = false)}>Cancel</Button>
		{#if printerList.length > 0}
			<Button variant="secondary" on:click={downloadPdf}>Download PDF</Button>
			<Button loading={printing} on:click={handlePrint}>Print</Button>
		{/if}
	</svelte:fragment>
</Modal>
