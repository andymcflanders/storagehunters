<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { locations } from '$lib/api';
	import { LocationCard, Card, MobileHome } from '$lib/components';
	import { _ } from '$lib/i18n';
	import type { Location } from '$lib/types';
	import type { DashboardStats } from '$lib/api/locations';

	let locationList: Location[] = [];
	let stats: DashboardStats | null = null;
	let loading = true;

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		try {
			[locationList, stats] = await Promise.all([
				locations.listLocations(),
				locations.getDashboardStats()
			]);
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Dashboard - StorageHub</title>
</svelte:head>

{#if $user}
	<!-- Mobile View -->
	<div class="md:hidden">
		<MobileHome />
	</div>

	<!-- Desktop View -->
	<div class="hidden md:block">
		<div class="space-y-8">
			<!-- Welcome -->
			<div>
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{$_('dashboard.welcome', { values: { name: $user.name } })}</h1>
				<p class="mt-1 text-slate-500 dark:text-slate-400">{$_('dashboard.subtitle')}</p>
			</div>

			<!-- Stats -->
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
							</svg>
						</div>
						<div>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats?.locations ?? '-'}</p>
							<p class="text-sm text-slate-500 dark:text-slate-400">{$_('dashboard.totalLocations')}</p>
						</div>
					</div>
				</Card>

				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
							</svg>
						</div>
						<div>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats?.containers ?? '-'}</p>
							<p class="text-sm text-slate-500 dark:text-slate-400">{$_('dashboard.totalContainers')}</p>
						</div>
					</div>
				</Card>

				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
							</svg>
						</div>
						<div>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats?.items ?? '-'}</p>
							<p class="text-sm text-slate-500 dark:text-slate-400">{$_('dashboard.totalItems')}</p>
						</div>
					</div>
				</Card>

				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
						<div>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats?.photos ?? '-'}</p>
							<p class="text-sm text-slate-500 dark:text-slate-400">{$_('dashboard.totalPhotos')}</p>
						</div>
					</div>
				</Card>
			</div>

			<!-- Locations -->
			<div>
				<div class="mb-4 flex items-center justify-between">
					<h2 class="text-lg font-semibold text-slate-900 dark:text-white">{$_('dashboard.yourLocations')}</h2>
					<a href="/locations" class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400">{$_('dashboard.viewAll')}</a>
				</div>

				{#if loading}
					<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{#each [1, 2, 3] as _}
							<div class="h-40 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-700"></div>
						{/each}
					</div>
				{:else if locationList.length === 0}
					<Card>
						<div class="py-8 text-center">
							<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
							</svg>
							<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">{$_('dashboard.noLocations')}</h3>
							<p class="mt-2 text-slate-500 dark:text-slate-400">{$_('dashboard.getStarted')}</p>
							<a href="/locations" class="btn-primary mt-4 inline-flex">{$_('locations.addLocation')}</a>
						</div>
					</Card>
				{:else}
					<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{#each locationList.slice(0, 6) as location}
							<LocationCard {location} containerCount={location.container_count} />
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
