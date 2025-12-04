<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { fade, scale } from 'svelte/transition';

	export let open = false;
	export let title = '';

	const dispatch = createEventDispatcher();

	function close() {
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-40 bg-black/50"
		transition:fade={{ duration: 200 }}
		on:click={close}
		on:keypress={close}
		role="button"
		tabindex="-1"
	/>

	<!-- Modal -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4"
		transition:scale={{ duration: 200, start: 0.95 }}
	>
		<div
			class="w-full max-w-lg rounded-xl bg-white shadow-xl"
			on:click|stopPropagation
			on:keypress|stopPropagation
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
		>
			<!-- Header -->
			{#if title}
				<div class="flex items-center justify-between border-b border-slate-200 px-6 py-4">
					<h2 id="modal-title" class="text-lg font-semibold text-slate-900">{title}</h2>
					<button
						type="button"
						class="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
						on:click={close}
					>
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				</div>
			{/if}

			<!-- Body -->
			<div class="p-6">
				<slot />
			</div>

			<!-- Footer -->
			{#if $$slots.footer}
				<div class="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
					<slot name="footer" />
				</div>
			{/if}
		</div>
	</div>
{/if}
