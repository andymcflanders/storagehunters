<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { Button } from '$lib/components';

	export let active = true;
	export let maxPhotosPerItem = 10;
	export let batchMode = false; // Enable batch mode for multiple items

	const dispatch = createEventDispatcher<{
		capture: { photos: File[] };
		batch: { items: File[][] }; // Array of items, each with array of photos
		error: { message: string };
		cancel: void;
	}>();

	let videoElement: HTMLVideoElement;
	let canvasElement: HTMLCanvasElement;
	let stream: MediaStream | null = null;
	let ready = false;
	let starting = false;
	let errorMessage = '';
	let hasCamera = true;

	// Current item's photos
	let currentPhotos: { file: File; preview: string }[] = [];

	// All items in batch mode
	let allItems: { photos: { file: File; preview: string }[] }[] = [];

	// Total counts for batch mode
	$: totalItems = allItems.length + (currentPhotos.length > 0 ? 1 : 0);
	$: totalPhotos = allItems.reduce((sum, item) => sum + item.photos.length, 0) + currentPhotos.length;

	onMount(async () => {
		if (active) {
			await startCamera();
		}
	});

	onDestroy(() => {
		stopCamera();
		cleanup();
	});

	function cleanup() {
		currentPhotos.forEach((p) => URL.revokeObjectURL(p.preview));
		allItems.forEach((item) => item.photos.forEach((p) => URL.revokeObjectURL(p.preview)));
	}

	$: if (active && !ready && !starting) {
		startCamera();
	} else if (!active && (ready || starting)) {
		stopCamera();
	}

	async function startCamera() {
		if (ready || starting) return;
		starting = true;
		errorMessage = '';

		try {
			if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
				throw new Error('Camera access not supported in this browser');
			}

			stream = await navigator.mediaDevices.getUserMedia({
				video: {
					facingMode: 'environment',
					width: { ideal: 1920 },
					height: { ideal: 1080 }
				}
			});

			if (!starting) {
				stream.getTracks().forEach((track) => track.stop());
				return;
			}

			videoElement.srcObject = stream;

			await new Promise<void>((resolve, reject) => {
				const onCanPlay = () => {
					videoElement.removeEventListener('canplay', onCanPlay);
					videoElement.removeEventListener('error', onError);
					resolve();
				};
				const onError = () => {
					videoElement.removeEventListener('canplay', onCanPlay);
					videoElement.removeEventListener('error', onError);
					reject(new Error('Video failed to load'));
				};
				videoElement.addEventListener('canplay', onCanPlay);
				videoElement.addEventListener('error', onError);

				if (videoElement.readyState >= 3) {
					videoElement.removeEventListener('canplay', onCanPlay);
					videoElement.removeEventListener('error', onError);
					resolve();
				}
			});

			if (!starting) {
				stream.getTracks().forEach((track) => track.stop());
				return;
			}

			try {
				await videoElement.play();
			} catch (playError) {
				if ((playError as Error).name !== 'AbortError') {
					throw playError;
				}
				return;
			}

			ready = true;
			starting = false;
		} catch (err) {
			starting = false;
			const error = err as Error;
			errorMessage = error.message || 'Failed to access camera';
			hasCamera = false;
			dispatch('error', { message: errorMessage });
		}
	}

	function stopCamera() {
		ready = false;
		starting = false;
		if (stream) {
			stream.getTracks().forEach((track) => track.stop());
			stream = null;
		}
		if (videoElement) {
			videoElement.srcObject = null;
		}
	}

	async function capturePhoto() {
		if (!ready || !videoElement || !canvasElement) return;
		if (currentPhotos.length >= maxPhotosPerItem) return;

		const ctx = canvasElement.getContext('2d');
		if (!ctx) return;

		canvasElement.width = videoElement.videoWidth;
		canvasElement.height = videoElement.videoHeight;
		ctx.drawImage(videoElement, 0, 0);

		const blob = await new Promise<Blob | null>((resolve) => {
			canvasElement.toBlob(resolve, 'image/jpeg', 0.9);
		});

		if (!blob) return;

		const filename = `photo-${Date.now()}.jpg`;
		const file = new File([blob], filename, { type: 'image/jpeg' });
		const preview = URL.createObjectURL(blob);

		currentPhotos = [...currentPhotos, { file, preview }];
	}

	function removePhoto(index: number) {
		const photo = currentPhotos[index];
		URL.revokeObjectURL(photo.preview);
		currentPhotos = currentPhotos.filter((_, i) => i !== index);
	}

	function nextItem() {
		if (currentPhotos.length === 0) return;

		// Save current item's photos
		allItems = [...allItems, { photos: [...currentPhotos] }];
		// Reset for next item
		currentPhotos = [];
	}

	function handleDone() {
		if (batchMode) {
			// Include current item if it has photos
			const finalItems = currentPhotos.length > 0
				? [...allItems, { photos: [...currentPhotos] }]
				: allItems;

			if (finalItems.length === 0) return;

			const itemFiles = finalItems.map((item) => item.photos.map((p) => p.file));
			dispatch('batch', { items: itemFiles });
		} else {
			if (currentPhotos.length === 0) return;
			const files = currentPhotos.map((p) => p.file);
			dispatch('capture', { photos: files });
		}
	}

	function handleCancel() {
		cleanup();
		currentPhotos = [];
		allItems = [];
		dispatch('cancel');
	}
</script>

<div class="flex flex-col h-full bg-black">
	<!-- Camera viewfinder -->
	<div class="relative flex-1 overflow-hidden">
		{#if errorMessage}
			<div class="flex h-full flex-col items-center justify-center bg-slate-900 p-6 text-center">
				<svg class="h-12 w-12 text-slate-500 dark:text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
				<p class="mt-4 text-sm text-slate-400">{errorMessage}</p>
				<button
					on:click={startCamera}
					class="mt-4 rounded-lg bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20"
				>
					Try Again
				</button>
			</div>
		{:else}
			<video
				bind:this={videoElement}
				class="h-full w-full object-cover"
				playsinline
				muted
			/>

			<!-- Status overlay -->
			{#if !ready}
				<div class="absolute inset-0 flex items-center justify-center bg-black/50">
					<div class="text-center text-white">
						<div class="h-8 w-8 mx-auto animate-spin rounded-full border-4 border-white border-t-transparent"></div>
						<p class="mt-3 text-sm">Starting camera...</p>
					</div>
				</div>
			{/if}

			<!-- Batch mode: Item counter -->
			{#if batchMode}
				<div class="absolute top-4 left-4 rounded-full bg-black/60 px-3 py-1.5 text-sm text-white">
					Item {totalItems > 0 ? totalItems : 1}
					{#if allItems.length > 0}
						<span class="text-slate-400">({allItems.length} saved)</span>
					{/if}
				</div>
			{/if}

			<!-- Photo count badge -->
			{#if currentPhotos.length > 0}
				<div class="absolute top-4 right-4 rounded-full bg-primary-600 px-3 py-1 text-sm font-medium text-white">
					{currentPhotos.length} photo{currentPhotos.length > 1 ? 's' : ''}
				</div>
			{/if}
		{/if}
	</div>

	<!-- Current item's photos strip -->
	{#if currentPhotos.length > 0}
		<div class="bg-slate-900 p-3">
			<div class="flex gap-2 overflow-x-auto pb-1">
				{#each currentPhotos as photo, index}
					<div class="relative flex-shrink-0">
						<img
							src={photo.preview}
							alt="Photo {index + 1}"
							class="h-16 w-16 rounded-lg object-cover"
						/>
						<button
							class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-white"
							on:click={() => removePhoto(index)}
						>
							<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Controls -->
	<div class="bg-slate-900 px-4 py-6 pb-safe">
		{#if batchMode}
			<!-- Batch mode controls -->
			<div class="flex items-center justify-between gap-3">
				<!-- Cancel -->
				<button
					class="rounded-full p-3 text-white hover:bg-white/10"
					on:click={handleCancel}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>

				<!-- Capture button -->
				<button
					class="flex h-16 w-16 items-center justify-center rounded-full bg-white dark:bg-slate-800 disabled:opacity-50"
					disabled={!ready || currentPhotos.length >= maxPhotosPerItem}
					on:click={capturePhoto}
				>
					<div class="h-14 w-14 rounded-full border-4 border-slate-900"></div>
				</button>

				<!-- Next Item / Done -->
				<div class="flex gap-2">
					{#if currentPhotos.length > 0}
						<button
							class="rounded-full bg-amber-600 px-4 py-2 text-sm font-medium text-white"
							on:click={nextItem}
						>
							Next Item
						</button>
					{/if}
					<button
						class="rounded-full bg-primary-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
						disabled={totalItems === 0 && currentPhotos.length === 0}
						on:click={handleDone}
					>
						Done
					</button>
				</div>
			</div>

			<p class="mt-3 text-center text-xs text-slate-400">
				{#if currentPhotos.length === 0 && allItems.length === 0}
					Take photos of an item, then tap "Next Item" for the next one
				{:else if currentPhotos.length === 0}
					{allItems.length} item{allItems.length > 1 ? 's' : ''} ready. Take photos of another item or tap "Done"
				{:else}
					Tap "Next Item" to save and photograph another item
				{/if}
			</p>
		{:else}
			<!-- Single item mode controls -->
			<div class="flex items-center justify-between gap-4">
				<button
					class="rounded-full p-3 text-white hover:bg-white/10"
					on:click={handleCancel}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>

				<button
					class="flex h-16 w-16 items-center justify-center rounded-full bg-white dark:bg-slate-800 disabled:opacity-50"
					disabled={!ready || currentPhotos.length >= maxPhotosPerItem}
					on:click={capturePhoto}
				>
					<div class="h-14 w-14 rounded-full border-4 border-slate-900"></div>
				</button>

				<button
					class="rounded-full bg-primary-600 px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
					disabled={currentPhotos.length === 0}
					on:click={handleDone}
				>
					Done ({currentPhotos.length})
				</button>
			</div>

			<p class="mt-3 text-center text-xs text-slate-400">
				{#if currentPhotos.length === 0}
					Take photos of your item from different angles
				{:else if currentPhotos.length < maxPhotosPerItem}
					Add more photos or tap Done
				{:else}
					Tap Done to continue
				{/if}
			</p>
		{/if}
	</div>

	<!-- Hidden canvas -->
	<canvas bind:this={canvasElement} class="hidden" />
</div>
