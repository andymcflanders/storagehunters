<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { locations } from '$lib/api';
	import { LocationCard, Button, Card, Input, Modal } from '$lib/components';
	import type { Location, LocationCreate } from '$lib/types';

	let locationList: Location[] = [];
	let loading = true;
	let showCreateModal = false;
	let creating = false;

	let newLocation: LocationCreate = {
		name: '',
		description: '',
		address: ''
	};

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadLocations();
	});

	async function loadLocations() {
		loading = true;
		try {
			locationList = await locations.listLocations();
		} finally {
			loading = false;
		}
	}

	async function handleCreate() {
		if (!newLocation.name.trim()) return;

		creating = true;
		try {
			await locations.createLocation(newLocation);
			toast.success('Location created successfully');
			showCreateModal = false;
			newLocation = { name: '', description: '', address: '' };
			await loadLocations();
		} catch (error) {
			toast.error('Failed to create location');
		} finally {
			creating = false;
		}
	}
</script>

<svelte:head>
	<title>Locations - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-slate-900">Locations</h1>
			<p class="mt-1 text-slate-500">Manage your storage locations</p>
		</div>
		<Button on:click={() => (showCreateModal = true)}>
			<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			Add Location
		</Button>
	</div>

	<!-- Locations Grid -->
	{#if loading}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each [1, 2, 3, 4, 5, 6] as _}
				<div class="h-40 animate-pulse rounded-xl bg-slate-200"></div>
			{/each}
		</div>
	{:else if locationList.length === 0}
		<Card>
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
				</svg>
				<h3 class="mt-4 text-lg font-medium text-slate-900">No locations yet</h3>
				<p class="mt-2 text-slate-500">Get started by adding your first storage location.</p>
				<Button class="mt-4" on:click={() => (showCreateModal = true)}>Add Location</Button>
			</div>
		</Card>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each locationList as location}
				<LocationCard {location} containerCount={location.container_count} />
			{/each}
		</div>
	{/if}
</div>

<!-- Create Modal -->
<Modal open={showCreateModal} title="Add Location" on:close={() => (showCreateModal = false)}>
	<form on:submit|preventDefault={handleCreate} class="space-y-4">
		<Input
			label="Name"
			placeholder="e.g., Garage, Loft, Storage Unit"
			bind:value={newLocation.name}
			required
			id="name"
		/>
		<Input
			label="Description"
			placeholder="Optional description"
			bind:value={newLocation.description}
			id="description"
		/>
		<Input
			label="Address"
			placeholder="Optional address for off-site storage"
			bind:value={newLocation.address}
			id="address"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showCreateModal = false)}>Cancel</Button>
		<Button loading={creating} on:click={handleCreate}>Create Location</Button>
	</svelte:fragment>
</Modal>
