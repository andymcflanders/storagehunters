<script lang="ts">
	function retry() {
		window.location.reload();
	}
</script>

<svelte:head>
	<title>Offline - StorageHub</title>
</svelte:head>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
	<div class="rounded-full bg-slate-100 dark:bg-slate-700 p-6">
		<svg class="h-16 w-16 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="1.5"
				d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a5 5 0 01-7.07-7.07m7.07 7.07l-2.828-2.828m0 0a3 3 0 014.243-4.243m-4.243 4.243L6.343 6.343"
			/>
		</svg>
	</div>

	<h1 class="mt-6 text-2xl font-bold text-slate-900 dark:text-white">You're offline</h1>
	<p class="mt-2 max-w-sm text-slate-500 dark:text-slate-400">
		Please check your internet connection and try again. Some features may be available from cache.
	</p>

	<button
		on:click={retry}
		class="mt-8 rounded-lg bg-primary-600 px-6 py-3 text-sm font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
	>
		Try Again
	</button>

	<p class="mt-8 text-sm text-slate-400">
		Tip: Recently viewed items and containers may still be accessible.
	</p>
</div>
