<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import * as printers from '$lib/api/printers';
	import { Card, Button, Input, Modal } from '$lib/components';
	import type { Printer, PrinterCreate, PrinterType, ConnectionType } from '$lib/types';

	let printerList: Printer[] = [];
	let loading = true;
	let showCreateModal = false;
	let showEditModal = false;
	let saving = false;
	let testing = false;
	let testingId = '';

	let editingPrinter: Printer | null = null;
	let formData: PrinterCreate = {
		name: '',
		printer_type: 'zebra_zpl',
		connection_type: 'network',
		address: '',
		label_width_mm: 50,
		label_height_mm: 25,
		is_default: false
	};

	const printerTypes: { value: PrinterType; label: string; description: string }[] = [
		{ value: 'zebra_zpl', label: 'Zebra (ZPL)', description: 'Zebra printers using ZPL language' },
		{ value: 'brother_ql', label: 'Brother QL', description: 'Brother QL series label printers' },
		{ value: 'network_ipp', label: 'Network Printer', description: 'Epson, HP, Canon via network/IPP' },
		{ value: 'generic_pdf', label: 'PDF (Download)', description: 'Generate PDF for any printer' }
	];

	const connectionTypes: { value: ConnectionType; label: string }[] = [
		{ value: 'network', label: 'Network (IP Address)' },
		{ value: 'usb', label: 'USB Connection' },
		{ value: 'file', label: 'File Output' }
	];

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadPrinters();
	});

	async function loadPrinters() {
		loading = true;
		try {
			printerList = await printers.getPrinters();
		} catch (error) {
			toast.error('Failed to load printers');
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		formData = {
			name: '',
			printer_type: 'zebra_zpl',
			connection_type: 'network',
			address: '',
			label_width_mm: 50,
			label_height_mm: 25,
			is_default: false
		};
	}

	function openCreateModal() {
		resetForm();
		editingPrinter = null;
		showCreateModal = true;
	}

	function openEditModal(printer: Printer) {
		editingPrinter = printer;
		formData = {
			name: printer.name,
			printer_type: printer.printer_type,
			connection_type: printer.connection_type,
			address: printer.address,
			label_width_mm: printer.label_width_mm,
			label_height_mm: printer.label_height_mm,
			is_default: printer.is_default
		};
		showEditModal = true;
	}

	async function handleSave() {
		if (!formData.name.trim() || !formData.address.trim()) {
			toast.warning('Please fill in all required fields');
			return;
		}

		saving = true;
		try {
			if (editingPrinter) {
				await printers.updatePrinter(editingPrinter.id, formData);
				toast.success('Printer updated');
				showEditModal = false;
			} else {
				await printers.createPrinter(formData);
				toast.success('Printer created');
				showCreateModal = false;
			}
			await loadPrinters();
		} catch (error) {
			toast.error(editingPrinter ? 'Failed to update printer' : 'Failed to create printer');
		} finally {
			saving = false;
		}
	}

	async function handleDelete(printer: Printer) {
		if (!confirm(`Delete printer "${printer.name}"?`)) return;

		try {
			await printers.deletePrinter(printer.id);
			toast.success('Printer deleted');
			await loadPrinters();
		} catch (error) {
			toast.error('Failed to delete printer');
		}
	}

	async function handleTest(printer: Printer) {
		testingId = printer.id;
		testing = true;
		try {
			const result = await printers.testPrinter(printer.id);
			if (result.success) {
				toast.success(result.message || 'Connection successful');
			} else {
				toast.error(result.message || 'Connection failed');
			}
		} catch (error) {
			toast.error('Failed to test printer');
		} finally {
			testing = false;
			testingId = '';
		}
	}

	async function handleSetDefault(printer: Printer) {
		try {
			await printers.updatePrinter(printer.id, { is_default: true });
			toast.success(`${printer.name} is now the default printer`);
			await loadPrinters();
		} catch (error) {
			toast.error('Failed to set default printer');
		}
	}

	function getPrinterTypeLabel(type: PrinterType): string {
		return printerTypes.find((t) => t.value === type)?.label || type;
	}

	function getConnectionTypeLabel(type: ConnectionType): string {
		return connectionTypes.find((t) => t.value === type)?.label || type;
	}

	function getAddressPlaceholder(connType: ConnectionType, printerType: PrinterType): string {
		if (printerType === 'generic_pdf') return 'download';
		if (printerType === 'network_ipp') {
			return connType === 'network'
				? '192.168.1.100 or ipp://printer.local/ipp/print'
				: 'EPSON_ET-2750';  // CUPS queue name
		}
		switch (connType) {
			case 'network':
				return '192.168.1.100:9100';
			case 'usb':
				return '/dev/usb/lp0';
			case 'file':
				return '/path/to/output.pdf';
			default:
				return '';
		}
	}
</script>

<svelte:head>
	<title>Printers - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Printers</h1>
			<p class="mt-1 text-slate-500 dark:text-slate-400">Configure label printers for container labels</p>
		</div>
		<Button on:click={openCreateModal}>
			<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			Add Printer
		</Button>
	</div>

	{#if loading}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each [1, 2, 3] as _}
				<div class="h-48 animate-pulse rounded-xl bg-slate-200"></div>
			{/each}
		</div>
	{:else if printerList.length === 0}
		<Card>
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
					/>
				</svg>
				<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">No printers configured</h3>
				<p class="mt-2 text-slate-500 dark:text-slate-400">Add a printer to start printing container labels.</p>
				<div class="mt-6">
					<Button on:click={openCreateModal}>Add Your First Printer</Button>
				</div>
			</div>
		</Card>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each printerList as printer}
				<Card>
					<div class="flex h-full flex-col">
						<div class="flex items-start justify-between">
							<div class="flex items-center gap-3">
								<div
									class="flex h-10 w-10 items-center justify-center rounded-lg
										{printer.printer_type === 'zebra_zpl'
										? 'bg-blue-100 text-blue-600'
										: printer.printer_type === 'brother_ql'
											? 'bg-green-100 text-green-600 dark:text-green-400'
											: printer.printer_type === 'network_ipp'
												? 'bg-orange-100 text-orange-600'
												: 'bg-purple-100 text-purple-600'}"
								>
									<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
										/>
									</svg>
								</div>
								<div>
									<h3 class="font-semibold text-slate-900 dark:text-white">
										{printer.name}
										{#if printer.is_default}
											<span
												class="ml-2 inline-flex items-center rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-700 dark:text-primary-300"
											>
												Default
											</span>
										{/if}
									</h3>
									<p class="text-sm text-slate-500 dark:text-slate-400">{getPrinterTypeLabel(printer.printer_type)}</p>
								</div>
							</div>
						</div>

						<div class="mt-4 flex-1 space-y-2 text-sm">
							<div class="flex justify-between">
								<span class="text-slate-500 dark:text-slate-400">Connection:</span>
								<span class="text-slate-700 dark:text-slate-300">{getConnectionTypeLabel(printer.connection_type)}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-slate-500 dark:text-slate-400">Address:</span>
								<span class="truncate text-slate-700 dark:text-slate-300" title={printer.address}>{printer.address}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-slate-500 dark:text-slate-400">Label Size:</span>
								<span class="text-slate-700 dark:text-slate-300">{printer.label_width_mm} x {printer.label_height_mm} mm</span>
							</div>
						</div>

						<div class="mt-4 flex gap-2 border-t border-slate-100 pt-4">
							<Button
								variant="secondary"
								size="sm"
								on:click={() => handleTest(printer)}
								loading={testing && testingId === printer.id}
							>
								Test
							</Button>
							{#if !printer.is_default}
								<Button variant="secondary" size="sm" on:click={() => handleSetDefault(printer)}>
									Set Default
								</Button>
							{/if}
							<div class="ml-auto flex gap-1">
								<button
									class="rounded p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
									on:click={() => openEditModal(printer)}
								>
									<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
										/>
									</svg>
								</button>
								<button
									class="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
									on:click={() => handleDelete(printer)}
								>
									<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
										/>
									</svg>
								</button>
							</div>
						</div>
					</div>
				</Card>
			{/each}
		</div>
	{/if}
</div>

<!-- Create/Edit Modal -->
<Modal
	open={showCreateModal || showEditModal}
	title={editingPrinter ? 'Edit Printer' : 'Add Printer'}
	on:close={() => {
		showCreateModal = false;
		showEditModal = false;
	}}
>
	<form on:submit|preventDefault={handleSave} class="space-y-4">
		<Input label="Printer Name" placeholder="e.g., Office Label Printer" bind:value={formData.name} required id="printer-name" />

		<div>
			<label for="printer-type" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Printer Type</label>
			<select
				id="printer-type"
				bind:value={formData.printer_type}
				class="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
			>
				{#each printerTypes as type}
					<option value={type.value}>{type.label} - {type.description}</option>
				{/each}
			</select>
		</div>

		{#if formData.printer_type !== 'generic_pdf'}
			<div>
				<label for="connection-type" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Connection Type</label>
				<select
					id="connection-type"
					bind:value={formData.connection_type}
					class="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				>
					{#each connectionTypes as type}
						<option value={type.value}>{type.label}</option>
					{/each}
				</select>
			</div>
		{/if}

		<Input
			label="Address"
			placeholder={getAddressPlaceholder(formData.connection_type, formData.printer_type)}
			bind:value={formData.address}
			required
			id="printer-address"
		/>

		<div class="grid grid-cols-2 gap-4">
			<Input
				label="Label Width (mm)"
				type="number"
				bind:value={formData.label_width_mm}
				required
				id="label-width"
			/>
			<Input
				label="Label Height (mm)"
				type="number"
				bind:value={formData.label_height_mm}
				required
				id="label-height"
			/>
		</div>

		<label class="flex items-center gap-2">
			<input type="checkbox" bind:checked={formData.is_default} class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400" />
			<span class="text-sm text-slate-700 dark:text-slate-300">Set as default printer</span>
		</label>
	</form>

	<svelte:fragment slot="footer">
		<Button
			variant="secondary"
			on:click={() => {
				showCreateModal = false;
				showEditModal = false;
			}}
		>
			Cancel
		</Button>
		<Button loading={saving} on:click={handleSave}>
			{editingPrinter ? 'Save Changes' : 'Add Printer'}
		</Button>
	</svelte:fragment>
</Modal>
