<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { auth, user } from '$lib/stores/auth';
	import { Toast, SearchBar, QuickAdd } from '$lib/components';
	import { setupI18n, setLocale, getStoredLocale, _, locale } from '$lib/i18n';
	import { isLoading } from 'svelte-i18n';
	import '../app.css';

	let menuOpen = false;
	let showQuickAdd = false;

	// Initialize i18n
	setupI18n();

	onMount(() => {
		auth.initialize();

		// After auth is initialized, sync language from user preference
		const unsubscribe = user.subscribe((u) => {
			if (u?.language) {
				setLocale(u.language);
			} else {
				// Fall back to stored locale or browser default
				const stored = getStoredLocale();
				if (stored) {
					setLocale(stored);
				}
			}
		});

		// First-run check: if the instance has no users yet, send the
		// browser into the setup wizard. The setup endpoints are public,
		// so this works even though there's nobody to authenticate as.
		// Skip the check on /setup itself to avoid redirect loops.
		if (!$page.url.pathname.startsWith('/setup')) {
			fetch('/api/setup/status', { credentials: 'include' })
				.then((r) => (r.ok ? r.json() : null))
				.then((data) => {
					if (data?.needs_setup) goto('/setup');
				})
				.catch(() => {
					// Backend unreachable — let the rest of the app surface that.
				});
		}

		return unsubscribe;
	});

	$: isLoginPage = $page.url.pathname === '/login';
	$: isSetupPage = $page.url.pathname.startsWith('/setup');
	$: isChromeless = isLoginPage || isSetupPage;
</script>

<Toast />

{#if !$user && !isChromeless}
	<!-- Redirect to login handled by layout load -->
{/if}

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
	{#if $user && !isChromeless}
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
					<span class="text-xl font-bold text-slate-900 dark:text-white">{$_('app.name')}</span>
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
								{#if $user.role === 'admin'}
									<a href="/admin" class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700">
										{$_('nav.admin')}
									</a>
								{/if}
								<a href="/settings" class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700">{$_('nav.settings')}</a>
								<button
									class="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700"
									on:click={() => auth.logout()}
								>
									{$_('nav.signOut')}
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
						{$_('nav.dashboard')}
					</a>
					<a
						href="/locations"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/locations')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.locations')}
					</a>
					<a
						href="/tags"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/tags')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.tags')}
					</a>
					<a
						href="/reminders"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/reminders')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.reminders')}
					</a>
					<a
						href="/printers"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/printers')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.printers')}
					</a>
					<a
						href="/godview"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/godview')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.godView')}
					</a>
					<a
						href="/outgrown"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/outgrown')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.outgrown')}
					</a>
					<a
						href="/declutter"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/declutter')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.declutter')}
					</a>
					<a
						href="/docs"
						class="flex items-center border-b-2 px-1 text-sm font-medium {$page.url.pathname.startsWith('/docs')
							? 'border-primary-500 text-primary-600'
							: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						{$_('nav.docs')}
					</a>
				</div>
			</div>
		</nav>
	{/if}

	<!-- Main content -->
	<main class="{$user && !isChromeless ? 'mx-auto max-w-7xl px-4 py-8 pb-24 sm:px-6 md:pb-8 lg:px-8' : ''}">
		<slot />
	</main>

	<!-- Mobile bottom navigation -->
	{#if $user && !isChromeless}
		<nav class="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-200 bg-white pb-safe dark:border-slate-700 dark:bg-slate-900 md:hidden">
			<div class="flex h-16 items-stretch justify-around">
				<!-- Home -->
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
					<span class="text-xs font-medium">{$_('nav.home')}</span>
				</a>

				<!-- Browse (Locations) -->
				<a
					href="/locations"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname.startsWith('/locations') ||
					$page.url.pathname.startsWith('/containers')
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
					</svg>
					<span class="text-xs font-medium">{$_('nav.browse')}</span>
				</a>

				<!-- Add (prominent center button) -->
				<button
					class="flex flex-1 flex-col items-center justify-center gap-1 text-slate-500 dark:text-slate-400"
					on:click={() => (showQuickAdd = true)}
				>
					<div class="flex h-12 w-12 -translate-y-2 items-center justify-center rounded-full bg-primary-600 text-white shadow-lg shadow-primary-600/30">
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
					</div>
					<span class="text-xs font-medium">{$_('nav.add')}</span>
				</button>

				<!-- Scan -->
				<a
					href="/scan"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname === '/scan'
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
						/>
					</svg>
					<span class="text-xs font-medium">{$_('nav.scan')}</span>
				</a>

				<!-- Declutter (Search remains accessible from the home screen) -->
				<a
					href="/declutter"
					class="flex flex-1 flex-col items-center justify-center gap-1 {$page.url.pathname.startsWith('/declutter')
						? 'text-primary-600'
						: 'text-slate-500 dark:text-slate-400'}"
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
						/>
					</svg>
					<span class="text-xs font-medium">{$_('nav.declutter')}</span>
				</a>
			</div>
		</nav>
	{/if}
</div>

<!-- QuickAdd Modal (mobile) -->
<QuickAdd bind:open={showQuickAdd} />
