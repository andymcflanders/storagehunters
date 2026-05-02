<script lang="ts">
	/**
	 * Lightweight wrapper around CameraCapture for picking a single photo.
	 *
	 * Used in places that previously had `<input type="file">` — e.g. the
	 * container create modals and the inline image swap on the container
	 * detail page. Matches the camera-driven flow already used for items
	 * so the UX is consistent across the app.
	 *
	 * Use `bind:value={file}` to get the picked File. Set `value = null`
	 * externally to clear it. The component dispatches `change` whenever
	 * the value changes — useful when the parent wants to upload immediately
	 * rather than collect a value into form state.
	 */

	import { createEventDispatcher, onDestroy } from 'svelte';
	import { _ } from '$lib/i18n';
	import CameraCapture from './CameraCapture.svelte';
	import Button from './ui/Button.svelte';

	export let value: File | null = null;

	const dispatch = createEventDispatcher<{
		change: { file: File | null };
	}>();

	let showCamera = false;
	let preview: string | null = null;
	let lastPreviewedFile: File | null = null;

	$: if (value !== lastPreviewedFile) {
		if (preview) {
			URL.revokeObjectURL(preview);
			preview = null;
		}
		if (value) {
			preview = URL.createObjectURL(value);
		}
		lastPreviewedFile = value;
	}

	onDestroy(() => {
		if (preview) URL.revokeObjectURL(preview);
	});

	function handleCapture(event: CustomEvent<{ photos: File[] }>) {
		const file = event.detail.photos[0] ?? null;
		value = file;
		dispatch('change', { file });
		showCamera = false;
	}

	function handleCameraCancel() {
		showCamera = false;
	}

	function handleClear() {
		value = null;
		dispatch('change', { file: null });
	}
</script>

{#if preview}
	<div class="space-y-2">
		<img
			src={preview}
			alt="Captured"
			class="aspect-[3/2] w-full rounded-lg object-cover"
		/>
		<div class="flex gap-2">
			<Button variant="secondary" type="button" on:click={() => (showCamera = true)}>
				{$_('containers.retakePhoto')}
			</Button>
			<Button variant="ghost" type="button" on:click={handleClear}>
				{$_('containers.removeImage')}
			</Button>
		</div>
	</div>
{:else}
	<Button variant="secondary" type="button" on:click={() => (showCamera = true)}>
		<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
			/>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
			/>
		</svg>
		{$_('containers.takePhoto')}
	</Button>
{/if}

{#if showCamera}
	<!-- Fullscreen overlay so the camera takes priority over any modal we're in. -->
	<div class="fixed inset-0 z-[100] bg-black">
		<CameraCapture
			active={showCamera}
			maxPhotosPerItem={1}
			on:capture={handleCapture}
			on:cancel={handleCameraCancel}
		/>
	</div>
{/if}
