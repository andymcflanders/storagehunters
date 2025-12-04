<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { auth, user } from '$lib/stores/auth';
	import { Toast, SearchBar } from '$lib/components';
	import '../app.css';

	let menuOpen = false;

	onMount(() => {
		auth.initialize();
	});

	$: isLoginPage = $page.url.pathname === '/login';
</script>

<Toast />

{#if !$user && !isLoginPage}
	<!-- Redirect to login handled by layout load -->
{/if}

<div class="min-h-screen bg-slate-50">
	{#if $user && !isLoginPage}
		<!-- Header -->
		<header class="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
			<div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
				<!-- Logo -->
				<a href="/" class="flex items-center gap-2">
					<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
							/>
						</svg>
					</div>
					<span class="text-xl font-bold text-slate-900">StorageHub</span>
				</a>

				<!-- Search (desktop) -->
				<div class="hidden flex-1 justify-center px-8 md:flex">
					<SearchBar />
				</div>

				<!-- User menu -->
				<div class="flex items-center gap-4">
					<a href="/search" class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 md:hidden">
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</a>

					<div class="relative">
						<button
							class="flex items-center gap-2 rounded-lg p-2 hover:bg-slate-100"
							on:click={() => (menuOpen = !menuOpen)}
						>
							<div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-600">
								{$user.name.charAt(0).toUpperCase()}
							</div>
							<span class="hidden text-sm font-medium text-slate-700 sm:inline">{$user.name}</span>
						</button>

						{#if menuOpen}
							<div class="absolute right-0 mt-2 w-48 rounded-lg bg-white py-1 shadow-lg ring-1 ring-black/5">
								<a href="/settings" class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">Settings</a>
								<button
									class="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
									on:click={() => auth.logout()}
								>
									Sign out
								</button>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</header>

		<!-- Navigation -->
		<nav class="border-b border-slate-200 bg-white">
			<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
				<div class="flex h-12 gap-6">
					<a
						href="/"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname === '/'
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					>
						Dashboard
					</a>
					<a
						href="/locations"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/locations')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					>
						Locations
					</a>
				</div>
			</div>
		</nav>
	{/if}

	<!-- Main content -->
	<main class="{$user && !isLoginPage ? 'mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8' : ''}">
		<slot />
	</main>
</div>
