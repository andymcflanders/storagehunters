<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { containers } from '$lib/api';
	import { QRScanner, Button, Card } from '$lib/components';

	let scanning = true;
	let lastScannedCode = '';
	let recentScans: { code: string; name: string; timestamp: Date }[] = [];

	onMount(() => {
		if (!$user) {
			goto('/login');
			return;
		}

		// Load recent scans from localStorage
		try {
			const stored = localStorage.getItem('storagehub_recent_scans');
			if (stored) {
				recentScans = JSON.parse(stored).map((s: { code: string; name: string; timestamp: string }) => ({
					...s,
					timestamp: new Date(s.timestamp)
				}));
			}
		} catch {
			// Ignore parse errors
		}
	});

	async function handleScan(event: CustomEvent<{ code: string }>) {
		const { code } = event.detail;

		// Avoid duplicate scans
		if (code === lastScannedCode) return;
		lastScannedCode = code;

		// Extract QR code from URL if it's a full URL
		let qrCode = code;
		try {
			const url = new URL(code);
			const match = url.pathname.match(/\/c\/([A-Z0-9]+)/i);
			if (match) {
				qrCode = match[1];
			}
		} catch {
			// Not a URL, use as-is
		}

		// Look up container
		try {
			const container = await containers.getContainerByQR(qrCode);
			if (container) {
				// Save to recent scans
				saveRecentScan(qrCode, container.name);

				// Navigate to container
				toast.success(`Found: ${container.name}`);
				goto(`/containers/${container.id}`);
			}
		} catch {
			toast.error('Container not found');
			// Reset for next scan
			setTimeout(() => {
				lastScannedCode = '';
			}, 2000);
		}
	}

	function handleError(event: CustomEvent<{ message: string }>) {
		toast.error(event.detail.message);
	}

	function saveRecentScan(code: string, name: string) {
		// Add to recent scans
		recentScans = [
			{ code, name, timestamp: new Date() },
			...recentScans.filter((s) => s.code !== code).slice(0, 9)
		];

		// Save to localStorage
		try {
			localStorage.setItem('storagehub_recent_scans', JSON.stringify(recentScans));
		} catch {
			// Ignore storage errors
		}
	}

	function clearRecentScans() {
		recentScans = [];
		localStorage.removeItem('storagehub_recent_scans');
	}

	function formatTime(date: Date): string {
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const minutes = Math.floor(diff / 60000);
		const hours = Math.floor(diff / 3600000);
		const days = Math.floor(diff / 86400000);

		if (minutes < 1) return 'Just now';
		if (minutes < 60) return `${minutes}m ago`;
		if (hours < 24) return `${hours}h ago`;
		return `${days}d ago`;
	}

	function handleManualSubmit(e: Event) {
		const form = e.target as HTMLFormElement;
		const input = form.elements.namedItem('code') as HTMLInputElement;
		if (input.value) {
			goto(`/c/${input.value.toUpperCase()}`);
		}
	}
</script>

<svelte:head>
	<title>Scan QR Code - StorageHub</title>
	<!-- Load jsQR library -->
	<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
</svelte:head>

<div class="mx-auto max-w-lg space-y-6">
	<!-- Header -->
	<div class="text-center">
		<h1 class="text-2xl font-bold text-slate-900">Scan QR Code</h1>
		<p class="mt-1 text-slate-500">Point your camera at a container label</p>
	</div>

	<!-- Scanner -->
	<QRScanner active={scanning} on:scan={handleScan} on:error={handleError} />

	<!-- Manual entry -->
	<Card>
		<form
			on:submit|preventDefault={handleManualSubmit}
			class="flex gap-2"
		>
			<input
				type="text"
				name="code"
				placeholder="Enter code manually"
				class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase placeholder:normal-case focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				pattern="[A-Za-z0-9]+"
			/>
			<Button type="submit">Go</Button>
		</form>
	</Card>

	<!-- Recent scans -->
	{#if recentScans.length > 0}
		<div>
			<div class="mb-3 flex items-center justify-between">
				<h2 class="text-sm font-medium text-slate-700">Recent Scans</h2>
				<button on:click={clearRecentScans} class="text-xs text-slate-400 hover:text-slate-600">
					Clear
				</button>
			</div>
			<div class="space-y-2">
				{#each recentScans as scan}
					<a
						href="/c/{scan.code}"
						class="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 hover:border-slate-300 hover:bg-slate-50"
					>
						<div>
							<p class="font-medium text-slate-900">{scan.name}</p>
							<p class="text-xs text-slate-400">{scan.code}</p>
						</div>
						<span class="text-xs text-slate-400">{formatTime(scan.timestamp)}</span>
					</a>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Tips -->
	<div class="rounded-lg bg-slate-100 p-4">
		<h3 class="text-sm font-medium text-slate-700">Tips</h3>
		<ul class="mt-2 space-y-1 text-sm text-slate-500">
			<li>Hold your phone steady about 6-12 inches from the code</li>
			<li>Ensure good lighting on the QR code</li>
			<li>The code should fit within the scanner frame</li>
		</ul>
	</div>
</div>
