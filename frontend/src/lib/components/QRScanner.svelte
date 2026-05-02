<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';

	export let active = true;

	const dispatch = createEventDispatcher<{
		scan: { code: string };
		error: { message: string };
	}>();

	let videoElement: HTMLVideoElement;
	let canvasElement: HTMLCanvasElement;
	let stream: MediaStream | null = null;
	let scanning = false;
	let starting = false;
	let errorMessage = '';
	let hasCamera = true;

	onMount(async () => {
		if (active) {
			await startScanner();
		}
	});

	onDestroy(() => {
		stopScanner();
	});

	$: if (active && !scanning && !starting) {
		startScanner();
	} else if (!active && (scanning || starting)) {
		stopScanner();
	}

	async function startScanner() {
		if (scanning || starting) return;
		starting = true;

		try {
			// Check for camera support
			if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
				throw new Error('Camera access not supported in this browser');
			}

			// Request camera access
			stream = await navigator.mediaDevices.getUserMedia({
				video: {
					facingMode: 'environment', // Prefer back camera
					width: { ideal: 1280 },
					height: { ideal: 720 }
				}
			});

			// Check if we were stopped while waiting for camera
			if (!starting) {
				stream.getTracks().forEach((track) => track.stop());
				return;
			}

			videoElement.srcObject = stream;

			// Wait for video to be ready before playing
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

				// If already ready, resolve immediately
				if (videoElement.readyState >= 3) {
					videoElement.removeEventListener('canplay', onCanPlay);
					videoElement.removeEventListener('error', onError);
					resolve();
				}
			});

			// Check again if we were stopped
			if (!starting) {
				stream.getTracks().forEach((track) => track.stop());
				return;
			}

			// Now safe to play
			try {
				await videoElement.play();
			} catch (playError) {
				// Ignore AbortError - happens when play is interrupted (e.g., component unmounted)
				if ((playError as Error).name !== 'AbortError') {
					throw playError;
				}
				return;
			}

			scanning = true;
			starting = false;
			errorMessage = '';

			// Start scanning loop
			requestAnimationFrame(scanFrame);
		} catch (err) {
			starting = false;
			const error = err as Error;
			errorMessage = error.message || 'Failed to access camera';
			hasCamera = false;
			dispatch('error', { message: errorMessage });
		}
	}

	function stopScanner() {
		scanning = false;
		starting = false;
		if (stream) {
			stream.getTracks().forEach((track) => track.stop());
			stream = null;
		}
		if (videoElement) {
			videoElement.srcObject = null;
		}
	}

	async function scanFrame() {
		if (!scanning || !videoElement || !canvasElement) return;

		if (videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
			const ctx = canvasElement.getContext('2d', { willReadFrequently: true });
			if (!ctx) return;

			canvasElement.width = videoElement.videoWidth;
			canvasElement.height = videoElement.videoHeight;

			ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
			const imageData = ctx.getImageData(0, 0, canvasElement.width, canvasElement.height);

			// Use jsQR library (loaded from CDN in scan page; types are declared
			// inline since the lib is loaded as a global, not bundled).
			type JsQRFn = (
				data: Uint8ClampedArray,
				width: number,
				height: number,
				options?: { inversionAttempts?: 'dontInvert' | 'attemptBoth' | 'invertFirst' | 'onlyInvert' }
			) => { data: string } | null;
			if (typeof window !== 'undefined' && 'jsQR' in window) {
				const jsQR = (window as unknown as { jsQR: JsQRFn }).jsQR;
				const code = jsQR(imageData.data, imageData.width, imageData.height, {
					inversionAttempts: 'dontInvert'
				});

				if (code && code.data) {
					// Found a QR code
					dispatch('scan', { code: code.data });
					// Brief pause before continuing to scan
					setTimeout(() => {
						if (scanning) requestAnimationFrame(scanFrame);
					}, 1000);
					return;
				}
			}
		}

		if (scanning) {
			requestAnimationFrame(scanFrame);
		}
	}

	function switchCamera() {
		stopScanner();
		// Toggle between front and back
		startScanner();
	}
</script>

<div class="relative overflow-hidden rounded-xl bg-black">
	{#if errorMessage}
		<div class="flex aspect-[4/3] flex-col items-center justify-center bg-slate-900 p-6 text-center">
			<svg class="h-12 w-12 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
				on:click={startScanner}
				class="mt-4 rounded-lg bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20"
			>
				Try Again
			</button>
		</div>
	{:else}
		<!-- Video feed -->
		<video
			bind:this={videoElement}
			class="aspect-[4/3] w-full object-cover"
			playsinline
			muted
		/>

		<!-- Scanning overlay -->
		<div class="pointer-events-none absolute inset-0 flex items-center justify-center">
			<!-- Corner markers -->
			<div class="relative h-48 w-48 sm:h-64 sm:w-64">
				<!-- Top-left -->
				<div class="absolute left-0 top-0 h-8 w-8 border-l-4 border-t-4 border-white/80"></div>
				<!-- Top-right -->
				<div class="absolute right-0 top-0 h-8 w-8 border-r-4 border-t-4 border-white/80"></div>
				<!-- Bottom-left -->
				<div class="absolute bottom-0 left-0 h-8 w-8 border-b-4 border-l-4 border-white/80"></div>
				<!-- Bottom-right -->
				<div class="absolute bottom-0 right-0 h-8 w-8 border-b-4 border-r-4 border-white/80"></div>

				<!-- Scanning line animation -->
				{#if scanning}
					<div class="animate-scan absolute left-2 right-2 h-0.5 bg-primary-400"></div>
				{/if}
			</div>
		</div>

		<!-- Status indicator -->
		<div class="absolute bottom-4 left-0 right-0 text-center">
			<span class="rounded-full bg-black/60 px-4 py-2 text-sm text-white">
				{#if scanning}
					Point camera at QR code
				{:else}
					Starting camera...
				{/if}
			</span>
		</div>
	{/if}

	<!-- Hidden canvas for processing -->
	<canvas bind:this={canvasElement} class="hidden" />
</div>

<style>
	@keyframes scan {
		0%,
		100% {
			top: 0.5rem;
		}
		50% {
			top: calc(100% - 0.5rem);
		}
	}

	.animate-scan {
		animation: scan 2s ease-in-out infinite;
	}
</style>
