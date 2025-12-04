<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { locations, containers } from '$lib/api';
	import { ContainerCard, Breadcrumb, Button, Card, Input, Modal } from '$lib/components';
	import type { LocationWithContainers, ContainerCreate } from '$lib/types';

	let location: LocationWithContainers | null = null;
	let loading = true;
	let showCreateModal = false;
	let creating = false;

	let newContainer: ContainerCreate = {
		name: '',
		location_id: '',
		notes: ''
	};

	$: locationId = $page.params.id;

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadLocation();
	});

	async function loadLocation() {
		loading = true;
		try {
			location = await locations.getLocation(locationId);
			newContainer.location_id = location.id;
		} catch {
			toast.error('Location not found');
			goto('/locations');
		} finally {
			loading = false;
		}
	}

	async function handleCreateContainer() {
		if (!newContainer.name.trim()) return;

		creating = true;
		try {
			await containers.createContainer(newContainer);
			toast.success('Container created successfully');
			showCreateModal = false;
			newContainer = { name: '', location_id: locationId, notes: '' };
			await loadLocation();
		} catch (error) {
			toast.error('Failed to create container');
		} finally {
			creating = false;
		}
	}
</script>

<svelte:head>
	<title>{location?.name ?? 'Location'} - StorageHub</title>
</svelte:head>

{#if loading}
	<div class="space-y-6">
		<div class="h-8 w-48 animate-pulse rounded bg-slate-200"></div>
		<div class="h-12 w-64 animate-pulse rounded bg-slate-200"></div>
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each [1, 2, 3] as _}
				<div class="h-32 animate-pulse rounded-xl bg-slate-200"></div>
			{/each}
		</div>
	</div>
{:else if location}
	<div class="space-y-6">
		<!-- Breadcrumb -->
		<Breadcrumb path={[]} currentName={location.name} />

		<!-- Header -->
		<div class="flex items-start justify-between">
			<div>
				<h1 class="text-2xl font-bold text-slate-900">{location.name}</h1>
				{#if location.description}
					<p class="mt-1 text-slate-500">{location.description}</p>
				{/if}
				{#if location.address}
					<p class="mt-2 flex items-center gap-1 text-sm text-slate-500">
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
						</svg>
						{location.address}
					</p>
				{/if}
			</div>
			<Button on:click={() => (showCreateModal = true)}>
				<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
				</svg>
				Add Container
			</Button>
		</div>

		<!-- Containers -->
		{#if location.containers.length === 0}
			<Card>
				<div class="py-12 text-center">
					<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
					</svg>
					<h3 class="mt-4 text-lg font-medium text-slate-900">No containers yet</h3>
					<p class="mt-2 text-slate-500">Add containers to organize items in this location.</p>
					<Button class="mt-4" on:click={() => (showCreateModal = true)}>Add Container</Button>
				</div>
			</Card>
		{:else}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{#each location.containers as container}
					<ContainerCard {container} />
				{/each}
			</div>
		{/if}
	</div>
{/if}

<!-- Create Container Modal -->
<Modal open={showCreateModal} title="Add Container" on:close={() => (showCreateModal = false)}>
	<form on:submit|preventDefault={handleCreateContainer} class="space-y-4">
		<Input
			label="Name"
			placeholder="e.g., Blue IKEA box, Clear bin #3"
			bind:value={newContainer.name}
			required
			id="container-name"
		/>
		<Input
			label="Notes"
			placeholder="Optional notes about this container"
			bind:value={newContainer.notes}
			id="container-notes"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showCreateModal = false)}>Cancel</Button>
		<Button loading={creating} on:click={handleCreateContainer}>Create Container</Button>
	</svelte:fragment>
</Modal>
