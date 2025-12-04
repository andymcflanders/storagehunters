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

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
	{#if $user && !isLoginPage}
		<!-- Header -->
		<header class="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
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
					<span class="text-xl font-bold text-slate-900 dark:text-white">StorageHub</span>
				</a>

				<!-- Search (desktop) -->
				<div class="hidden flex-1 justify-center px-8 md:flex">
					<SearchBar />
				</div>

				<!-- User menu -->
				<div class="flex items-center gap-4">
					<a href="/search" class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 md:hidden">
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</a>

					<div class="relative">
						<button
							class="flex items-center gap-2 rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
							on:click={() => (menuOpen = !menuOpen)}
						>
							<div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-600 dark:bg-primary-900 dark:text-primary-400">
								{$user.name.charAt(0).toUpperCase()}
							</div>
							<span class="hidden text-sm font-medium text-slate-700 dark:text-slate-300 sm:inline">{$user.name}</span>
						</button>

						{#if menuOpen}
							<div class="absolute right-0 mt-2 w-48 rounded-lg bg-white py-1 shadow-lg ring-1 ring-black/5 dark:bg-slate-800 dark:ring-slate-700">
								<a href="/settings" class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700">Settings</a>
								<button
									class="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
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

		<!-- Navigation (desktop) -->
		<nav class="hidden border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 md:block">
			<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
				<div class="flex h-12 gap-6">
					<a
						href="/"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname === '/'
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						Dashboard
					</a>
					<a
						href="/locations"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/locations')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						Locations
					</a>
					<a
						href="/tags"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/tags')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						Tags
					</a>
					<a
						href="/printers"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/printers')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						Printers
					</a>
				</div>
			</div>
		</nav>
	{/if}

	<!-- Main content -->
	<main class="{$user && !isLoginPage ? 'mx-auto max-w-7xl px-4 py-8 pb-24 sm:px-6 md:pb-8 lg:px-8' : ''}">
		<slot />
	</main>

	<!-- Mobile bottom navigation -->
	{#if $user && !isLoginPage}
		<nav class="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-200 bg-white pb-safe dark:border-slate-700 dark:bg-slate-900 md:hidden">
			<div class="flex h-16 items-stretch justify-around">
				<a
					href="/"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname === '/'
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
						/>
					</svg>
					<span class="text-xs font-medium">Home</span>
				</a>

				<a
					href="/locations"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname.startsWith('/locations') ||
					$page.url.pathname.startsWith('/containers')
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
						/>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
					<span class="text-xs font-medium">Locations</span>
				</a>

				<a
					href="/scan"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname === '/scan'
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<div
						class="flex h-12 w-12 -translate-y-2 items-center justify-center rounded-full {$page.url.pathname === '/scan'
							? 'bg-primary-600 text-white'
							: 'bg-primary-100 text-primary-600 dark:bg-primary-900'} shadow-lg"
					>
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
							/>
						</svg>
					</div>
					<span class="text-xs font-medium">Scan</span>
				</a>

				<a
					href="/search"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname === '/search'
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<span class="text-xs font-medium">Search</span>
				</a>

				<a
					href="/printers"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname.startsWith('/printers')
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
						/>
					</svg>
					<span class="text-xs font-medium">Print</span>
				</a>
			</div>
		</nav>
	{/if}
</div>
