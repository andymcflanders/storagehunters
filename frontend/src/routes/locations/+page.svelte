<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { locations } from '$lib/api';
	import { LocationCard, Button, Card, Input, Modal } from '$lib/components';
	import { _ } from '$lib/i18n';
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
			<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{$_('locations.title')}</h1>
			<p class="mt-1 text-slate-500 dark:text-slate-400">{$_('locations.manageStorage')}</p>
		</div>
		<Button on:click={() => (showCreateModal = true)}>
			<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			{$_('locations.addLocation')}
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
				<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">{$_('dashboard.noLocations')}</h3>
				<p class="mt-2 text-slate-500 dark:text-slate-400">{$_('dashboard.getStarted')}</p>
				<Button class="mt-4" on:click={() => (showCreateModal = true)}>{$_('locations.addLocation')}</Button>
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
<Modal open={showCreateModal} title={$_('locations.addLocation')} on:close={() => (showCreateModal = false)}>
	<form on:submit|preventDefault={handleCreate} class="space-y-4">
		<Input
			label={$_('common.name')}
			placeholder={$_('locations.namePlaceholder')}
			bind:value={newLocation.name}
			required
			id="name"
		/>
		<Input
			label={$_('common.description')}
			placeholder={$_('locations.descriptionPlaceholder')}
			bind:value={newLocation.description}
			id="description"
		/>
		<Input
			label={$_('locations.address')}
			placeholder={$_('locations.addressPlaceholder')}
			bind:value={newLocation.address}
			id="address"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showCreateModal = false)}>{$_('common.cancel')}</Button>
		<Button loading={creating} on:click={handleCreate}>{$_('common.create')}</Button>
	</svelte:fragment>
</Modal>
