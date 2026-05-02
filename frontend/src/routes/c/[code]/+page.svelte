<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from '$lib/stores/toast';
	import { containers } from '$lib/api';

	let loading = true;
	let error = '';

	$: code = $page.params.code!;

	onMount(async () => {
		await lookupContainer();
	});

	async function lookupContainer() {
		loading = true;
		error = '';

		try {
			const container = await containers.getContainerByQR(code);
			if (container) {
				goto(`/containers/${container.id}`, { replaceState: true });
			} else {
				error = 'Container not found';
			}
		} catch (err) {
			error = 'Container not found';
			toast.error('Could not find container with this QR code');
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Looking up container... - StorageHub</title>
</svelte:head>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
	{#if loading}
		<div class="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
		<p class="mt-4 text-slate-500">Looking up container...</p>
		<p class="mt-2 font-mono text-sm text-slate-400">{code}</p>
	{:else if error}
		<div class="rounded-full bg-red-100 p-6">
			<svg class="h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
		</div>
		<h1 class="mt-6 text-xl font-bold text-slate-900">Container Not Found</h1>
		<p class="mt-2 text-slate-500">
			No container matches the QR code <span class="font-mono">{code}</span>
		</p>
		<div class="mt-6 flex gap-3">
			<a
				href="/scan"
				class="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
			>
				Scan Again
			</a>
			<a
				href="/"
				class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
			>
				Go Home
			</a>
		</div>
	{/if}
</div>
