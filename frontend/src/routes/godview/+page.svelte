<script lang="ts">
	import { onMount } from 'svelte';
	import { inventory, locations, containers, items } from '$lib/api';
	import GodViewToolbar from '$lib/components/godview/GodViewToolbar.svelte';
	import GodViewLocationRow from '$lib/components/godview/GodViewLocationRow.svelte';
	import DeleteContainerModal from '$lib/components/godview/DeleteContainerModal.svelte';
	import type { DeleteMode } from '$lib/api/containers';
	import type {
		GodViewResponse,
		GodViewLocation,
		GodViewContainer,
		GodViewItem,
		GodViewUserInfo,
		Condition,
		Seasonal
	} from '$lib/types';

	let data: GodViewResponse | null = null;
	let loading = true;
	let error: string | null = null;

	// Filter state
	let searchQuery = '';
	let filterCondition: Condition | '' = '';
	let filterSeasonal: Seasonal | '' = '';
	let filterOwner = '';
	let filterNeedsReview: boolean | null = null;
	let filterLocationIds: Set<string> = new Set();
	let filterContainerIds: Set<string> = new Set();

	// Expand/collapse state
	let expandedLocations = new Set<string>();
	let expandedContainers = new Set<string>();
	let expandedItems = new Set<string>();
	let allLocationsExpanded = true;
	let allContainersExpanded = true;

	// Filtered data
	let filteredLocations: GodViewLocation[] = [];

	// Delete container modal state
	let deleteModalContainer: { id: string; name: string; itemCount: number; childCount: number } | null = null;

	async function loadData(preserveExpandState = false) {
		loading = true;
		error = null;
		try {
			const prevExpandedLocations = expandedLocations;
			const prevExpandedContainers = expandedContainers;

			data = await inventory.getInventoryTree();

			if (preserveExpandState) {
				// Keep existing expand states, just add new containers as expanded
				const allContainerIds = new Set<string>();
				for (const location of data.locations) {
					collectContainerIds(location.containers, allContainerIds);
				}
				// Add any new containers to the expanded set
				for (const id of allContainerIds) {
					if (!prevExpandedContainers.has(id)) {
						prevExpandedContainers.add(id);
					}
				}
				expandedLocations = prevExpandedLocations;
				expandedContainers = prevExpandedContainers;
			} else {
				// Initially expand all locations
				expandedLocations = new Set(data.locations.map((l) => l.id));
				// Initially expand all containers (recursive)
				expandedContainers = new Set<string>();
				for (const location of data.locations) {
					collectContainerIds(location.containers, expandedContainers);
				}
			}
			applyFilters();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load inventory';
		} finally {
			loading = false;
		}
	}

	function collectContainerIds(containerList: GodViewContainer[], idSet: Set<string>) {
		for (const container of containerList) {
			idSet.add(container.id);
			collectContainerIds(container.children, idSet);
		}
	}

	function applyFilters() {
		if (!data) {
			filteredLocations = [];
			return;
		}

		// Deep clone and filter the data
		filteredLocations = data.locations
			.map((location) => filterLocation(location))
			.filter((location) => location !== null) as GodViewLocation[];
	}

	function filterLocation(location: GodViewLocation): GodViewLocation | null {
		// If location filter is active and this location is not selected, skip it
		if (filterLocationIds.size > 0 && !filterLocationIds.has(location.id)) {
			return null;
		}

		const filteredContainers = location.containers
			.map((container) => filterContainer(container, location.id))
			.filter((c) => c !== null) as GodViewContainer[];

		// If location name matches search, include it even if no containers match
		const locationMatches = searchQuery === '' || location.name.toLowerCase().includes(searchQuery.toLowerCase());

		if (filteredContainers.length === 0 && !locationMatches) {
			return null;
		}

		return {
			...location,
			containers: filteredContainers
		};
	}

	function filterContainer(container: GodViewContainer, locationId: string): GodViewContainer | null {
		// When container filter is active, only show selected containers (not parents)
		const isDirectlySelected = filterContainerIds.has(container.id);
		const hasSelectedDescendant = filterContainerIds.size > 0 && !isDirectlySelected && hasDescendantInFilter(container);

		// If container filter is active
		if (filterContainerIds.size > 0) {
			// If this container is directly selected, show it with all its items
			if (isDirectlySelected) {
				const filteredItems = container.items.filter((item) => itemMatchesFilters(item, container.id, true));
				const filteredChildren = container.children
					.map((child) => filterContainer(child, locationId))
					.filter((c) => c !== null) as GodViewContainer[];

				return {
					...container,
					items: filteredItems,
					children: filteredChildren
				};
			}
			// If it has selected descendants, recurse but don't show this container's items
			if (hasSelectedDescendant) {
				const filteredChildren = container.children
					.map((child) => filterContainer(child, locationId))
					.filter((c) => c !== null) as GodViewContainer[];

				if (filteredChildren.length === 0) {
					return null;
				}

				return {
					...container,
					items: [], // Don't show items from non-selected parent containers
					children: filteredChildren
				};
			}
			// Not selected and no selected descendants
			return null;
		}

		// No container filter - show everything that matches other filters
		const filteredItems = container.items.filter((item) => itemMatchesFilters(item, container.id, false));
		const filteredChildren = container.children
			.map((child) => filterContainer(child, locationId))
			.filter((c) => c !== null) as GodViewContainer[];

		// Container matches if name matches search
		const containerMatches = searchQuery === '' || container.name.toLowerCase().includes(searchQuery.toLowerCase());

		if (filteredItems.length === 0 && filteredChildren.length === 0 && !containerMatches) {
			return null;
		}

		return {
			...container,
			items: filteredItems,
			children: filteredChildren
		};
	}

	// Check if any descendant container is in the filter
	function hasDescendantInFilter(container: GodViewContainer): boolean {
		for (const child of container.children) {
			if (filterContainerIds.has(child.id) || hasDescendantInFilter(child)) {
				return true;
			}
		}
		return false;
	}

	function itemMatchesFilters(item: GodViewItem, containerId: string, containerIsSelected: boolean): boolean {
		// When container filter is active, we already filtered at container level
		// so only check if the container is directly selected
		if (filterContainerIds.size > 0 && !containerIsSelected) {
			return false;
		}

		// Search filter
		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			const searchFields = [item.name, item.description, item.ai_name, item.ai_name_no, item.ai_description, item.ai_description_no].filter(Boolean);
			if (!searchFields.some((field) => field?.toLowerCase().includes(query))) {
				return false;
			}
		}

		// Condition filter
		if (filterCondition && item.condition !== filterCondition) {
			return false;
		}

		// Seasonal filter
		if (filterSeasonal && item.seasonal !== filterSeasonal) {
			return false;
		}

		// Owner filter
		if (filterOwner) {
			if (filterOwner === 'unassigned') {
				if (item.owner_id !== null) return false;
			} else if (item.owner_id !== filterOwner) {
				return false;
			}
		}

		// Needs review filter
		if (filterNeedsReview !== null && item.needs_review !== filterNeedsReview) {
			return false;
		}

		return true;
	}

	// Update handlers
	async function handleUpdateLocation(e: CustomEvent<{ id: string; field: string; value: string }>) {
		const { id, field, value } = e.detail;
		try {
			await locations.updateLocation(id, { [field]: value });
			await loadData();
		} catch (err) {
			console.error('Failed to update location:', err);
		}
	}

	async function handleDeleteLocation(e: CustomEvent<{ id: string }>) {
		try {
			await locations.deleteLocation(e.detail.id);
			await loadData();
		} catch (err) {
			console.error('Failed to delete location:', err);
		}
	}

	async function handleUpdateContainer(e: CustomEvent<{ id: string; field: string; value: string }>) {
		const { id, field, value } = e.detail;
		try {
			await containers.updateContainer(id, { [field]: value });
			await loadData();
		} catch (err) {
			console.error('Failed to update container:', err);
		}
	}

	function handleDeleteContainer(e: CustomEvent<{ id: string; name: string; itemCount: number; childCount: number }>) {
		// Show delete modal
		deleteModalContainer = e.detail;
	}

	async function handleDeleteContainerConfirm(e: CustomEvent<{ mode: DeleteMode; transferTo?: string }>) {
		if (!deleteModalContainer) return;

		try {
			await containers.deleteContainer(deleteModalContainer.id, {
				mode: e.detail.mode,
				transferTo: e.detail.transferTo
			});
			deleteModalContainer = null;
			await loadData(true);
		} catch (err) {
			console.error('Failed to delete container:', err);
			alert('Failed to delete container: ' + (err instanceof Error ? err.message : 'Unknown error'));
		}
	}

	function handleDeleteContainerCancel() {
		deleteModalContainer = null;
	}

	// Get all containers for the transfer dropdown (excluding the one being deleted)
	function getAvailableContainersForTransfer(): { id: string; name: string; depth: number }[] {
		if (!data || !deleteModalContainer) return [];

		const result: { id: string; name: string; depth: number }[] = [];

		function collectContainers(containerList: GodViewContainer[], depth: number) {
			for (const container of containerList) {
				if (container.id !== deleteModalContainer!.id) {
					result.push({ id: container.id, name: container.name, depth });
					collectContainers(container.children, depth + 1);
				}
			}
		}

		for (const location of data.locations) {
			collectContainers(location.containers, 0);
		}

		return result;
	}

	async function handleUpdateItem(e: CustomEvent<{ id: string; field: string; value: string | number | null }>) {
		const { id, field, value } = e.detail;
		try {
			await items.updateItem(id, { [field]: value });
			await loadData();
		} catch (err) {
			console.error('Failed to update item:', err);
		}
	}

	async function handleDeleteItem(e: CustomEvent<{ id: string }>) {
		try {
			await items.deleteItem(e.detail.id);
			await loadData();
		} catch (err) {
			console.error('Failed to delete item:', err);
		}
	}

	async function handleMoveItem(e: CustomEvent<{ itemId: string; targetContainerId: string }>) {
		const { itemId, targetContainerId } = e.detail;
		try {
			await items.moveItem(itemId, targetContainerId);
			await loadData();
		} catch (err) {
			console.error('Failed to move item:', err);
		}
	}

	async function handleCreateContainer(e: CustomEvent<{ locationId: string }>) {
		const name = prompt('Enter container name:');
		if (!name) return;

		try {
			await containers.createContainer({
				name,
				location_id: e.detail.locationId
			});
			await loadData(true);
		} catch (err) {
			console.error('Failed to create container:', err);
		}
	}

	async function handleCreateLocation() {
		const name = prompt('Enter location name:');
		if (!name) return;

		try {
			const newLocation = await locations.createLocation({ name });
			await loadData(true);
			// Expand the new location
			expandedLocations.add(newLocation.id);
			expandedLocations = expandedLocations;
		} catch (err) {
			console.error('Failed to create location:', err);
		}
	}

	function handleToggleItemExpand(e: CustomEvent<{ id: string }>) {
		const { id } = e.detail;
		if (expandedItems.has(id)) {
			expandedItems.delete(id);
		} else {
			expandedItems.add(id);
		}
		expandedItems = expandedItems; // Trigger reactivity
	}

	function handleToggleContainerExpand(e: CustomEvent<{ id: string }>) {
		const { id } = e.detail;
		if (expandedContainers.has(id)) {
			expandedContainers.delete(id);
		} else {
			expandedContainers.add(id);
		}
		expandedContainers = expandedContainers;
		updateContainerExpandState();
	}

	function handleToggleLocationExpand(e: CustomEvent<{ id: string }>) {
		const { id } = e.detail;
		if (expandedLocations.has(id)) {
			expandedLocations.delete(id);
		} else {
			expandedLocations.add(id);
		}
		expandedLocations = expandedLocations;
		updateLocationExpandState();
	}

	function updateLocationExpandState() {
		if (!data) return;
		allLocationsExpanded = data.locations.every((l) => expandedLocations.has(l.id));
	}

	function updateContainerExpandState() {
		if (!data) return;
		const allContainers = new Set<string>();
		for (const location of data.locations) {
			collectContainerIds(location.containers, allContainers);
		}
		allContainersExpanded = [...allContainers].every((id) => expandedContainers.has(id));
	}

	function expandAllLocations() {
		if (!data) return;
		expandedLocations = new Set(data.locations.map((l) => l.id));
		allLocationsExpanded = true;
	}

	function collapseAllLocations() {
		expandedLocations = new Set();
		allLocationsExpanded = false;
	}

	function expandAllContainers() {
		if (!data) return;
		expandedContainers = new Set<string>();
		for (const location of data.locations) {
			collectContainerIds(location.containers, expandedContainers);
		}
		allContainersExpanded = true;
	}

	function collapseAllContainers() {
		expandedContainers = new Set();
		allContainersExpanded = false;
	}

	// Reactive filter application
	$: if (data) {
		searchQuery;
		filterCondition;
		filterSeasonal;
		filterOwner;
		filterNeedsReview;
		filterLocationIds;
		filterContainerIds;
		applyFilters();
	}

	onMount(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>God View - StorageHub</title>
</svelte:head>

<div class="min-h-screen bg-slate-100 dark:bg-slate-900">
	<!-- Header -->
	<div class="border-b border-slate-200 bg-white px-6 py-4 dark:border-slate-700 dark:bg-slate-800">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white">God View</h1>
				<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Complete inventory hierarchy - edit anything inline</p>
			</div>
			<div class="flex items-center gap-3">
				<button
					class="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
					on:click={handleCreateLocation}
				>
					<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
					</svg>
					New Location
				</button>
				<a href="/" class="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700">
					Back to Dashboard
				</a>
			</div>
		</div>
	</div>

	<div class="p-6">
		{#if loading}
			<div class="flex items-center justify-center py-20">
				<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
				<span class="ml-3 text-slate-500 dark:text-slate-400">Loading inventory...</span>
			</div>
		{:else if error}
			<div class="rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20">
				<p class="text-red-600 dark:text-red-400">{error}</p>
				<button class="mt-4 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700" on:click={loadData}>
					Retry
				</button>
			</div>
		{:else if data}
			<!-- Toolbar -->
			<GodViewToolbar
				users={data.users}
				locations={data.locations}
				totalLocations={data.total_locations}
				totalContainers={data.total_containers}
				totalItems={data.total_items}
				{searchQuery}
				{filterCondition}
				{filterSeasonal}
				{filterOwner}
				{filterNeedsReview}
				{filterLocationIds}
				{filterContainerIds}
				{allLocationsExpanded}
				{allContainersExpanded}
				on:search={(e) => (searchQuery = e.detail)}
				on:filterCondition={(e) => (filterCondition = e.detail)}
				on:filterSeasonal={(e) => (filterSeasonal = e.detail)}
				on:filterOwner={(e) => (filterOwner = e.detail)}
				on:filterNeedsReview={(e) => (filterNeedsReview = e.detail)}
				on:filterLocationIds={(e) => (filterLocationIds = e.detail)}
				on:filterContainerIds={(e) => (filterContainerIds = e.detail)}
				on:expandAllLocations={expandAllLocations}
				on:collapseAllLocations={collapseAllLocations}
				on:expandAllContainers={expandAllContainers}
				on:collapseAllContainers={collapseAllContainers}
				on:refresh={loadData}
			/>

			<!-- Table -->
			<div class="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
				<table class="w-full min-w-[1000px]">
					<thead class="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900">
						<tr>
							<th class="w-16 px-2 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400"></th>
							<th class="w-12 px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400"></th>
							<th class="min-w-[150px] max-w-[200px] px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Name</th>
							<th class="min-w-[150px] max-w-[250px] px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Description</th>
							<th class="w-20 px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Size</th>
							<th class="w-28 px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Condition</th>
							<th class="w-24 px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Seasonal</th>
							<th class="w-28 px-1 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Owner</th>
							<th class="w-16 px-2 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400"></th>
						</tr>
					</thead>
					<tbody>
						{#if filteredLocations.length === 0}
							<tr>
								<td colspan="9" class="py-12 text-center text-slate-500 dark:text-slate-400">
									{#if searchQuery || filterCondition || filterSeasonal || filterOwner || filterNeedsReview !== null || filterLocationIds.size > 0 || filterContainerIds.size > 0}
										No items match your filters
									{:else}
										No inventory data found
									{/if}
								</td>
							</tr>
						{:else}
							{#each filteredLocations as location (location.id)}
								<GodViewLocationRow
									{location}
									users={data.users}
									expanded={expandedLocations.has(location.id)}
									{expandedContainers}
									{expandedItems}
									on:updateLocation={handleUpdateLocation}
									on:deleteLocation={handleDeleteLocation}
									on:updateContainer={handleUpdateContainer}
									on:deleteContainer={handleDeleteContainer}
									on:createContainer={handleCreateContainer}
									on:updateItem={handleUpdateItem}
									on:deleteItem={handleDeleteItem}
									on:toggleItemExpand={handleToggleItemExpand}
									on:toggleContainerExpand={handleToggleContainerExpand}
									on:toggleLocationExpand={handleToggleLocationExpand}
									on:moveItem={handleMoveItem}
								/>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<!-- Delete Container Modal -->
{#if deleteModalContainer}
	<DeleteContainerModal
		containerName={deleteModalContainer.name}
		itemCount={deleteModalContainer.itemCount}
		childCount={deleteModalContainer.childCount}
		availableContainers={getAvailableContainersForTransfer()}
		on:confirm={handleDeleteContainerConfirm}
		on:cancel={handleDeleteContainerCancel}
	/>
{/if}
