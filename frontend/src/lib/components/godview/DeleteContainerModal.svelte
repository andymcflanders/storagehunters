<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { DeleteMode } from '$lib/api/containers';

	export let containerName: string;
	export let itemCount: number;
	export let childCount: number;
	export let availableContainers: { id: string; name: string; depth: number }[] = [];

	const dispatch = createEventDispatcher<{
		confirm: { mode: DeleteMode; transferTo?: string };
		cancel: void;
	}>();

	let selectedMode: DeleteMode = 'recursive';
	let selectedTransferContainer: string = '';
	let isDeleting = false;

	$: hasContents = itemCount > 0 || childCount > 0;
	$: canTransfer = availableContainers.length > 0 && itemCount > 0;

	function handleConfirm() {
		if (selectedMode === 'transfer' && !selectedTransferContainer) {
			return;
		}
		isDeleting = true;
		dispatch('confirm', {
			mode: selectedMode,
			transferTo: selectedMode === 'transfer' ? selectedTransferContainer : undefined
		});
	}

	function handleCancel() {
		dispatch('cancel');
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			handleCancel();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div
	class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
	on:click|self={handleCancel}
	role="dialog"
	aria-modal="true"
	aria-labelledby="modal-title"
>
	<div class="w-full max-w-md rounded-xl bg-white shadow-xl dark:bg-slate-800">
		<!-- Header -->
		<div class="border-b border-slate-200 p-4 dark:border-slate-700">
			<h2 id="modal-title" class="text-lg font-semibold text-slate-900 dark:text-white">
				Delete Container
			</h2>
		</div>

		<!-- Content -->
		<div class="p-4">
			<p class="mb-4 text-slate-700 dark:text-slate-300">
				Are you sure you want to delete <strong class="text-slate-900 dark:text-white">{containerName}</strong>?
			</p>

			{#if hasContents}
				<div class="mb-4 rounded-lg bg-amber-50 p-3 dark:bg-amber-900/20">
					<div class="flex items-start gap-2">
						<svg class="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
						</svg>
						<div class="text-sm text-amber-800 dark:text-amber-200">
							<p class="font-medium">This container has contents:</p>
							<ul class="mt-1 list-inside list-disc">
								{#if itemCount > 0}
									<li>{itemCount} item{itemCount !== 1 ? 's' : ''}</li>
								{/if}
								{#if childCount > 0}
									<li>{childCount} nested container{childCount !== 1 ? 's' : ''}</li>
								{/if}
							</ul>
						</div>
					</div>
				</div>

				<div class="space-y-3">
					<p class="text-sm font-medium text-slate-700 dark:text-slate-300">What would you like to do?</p>

					<!-- Delete All Option -->
					<label class="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 p-3 hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-700/50">
						<input
							type="radio"
							name="deleteMode"
							value="recursive"
							bind:group={selectedMode}
							class="mt-1"
						/>
						<div>
							<span class="font-medium text-slate-900 dark:text-white">Delete everything</span>
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Permanently delete this container and all its contents (items and nested containers)
							</p>
						</div>
					</label>

					<!-- Transfer Option -->
					{#if canTransfer}
						<label class="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 p-3 hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-700/50">
							<input
								type="radio"
								name="deleteMode"
								value="transfer"
								bind:group={selectedMode}
								class="mt-1"
							/>
							<div class="flex-1">
								<span class="font-medium text-slate-900 dark:text-white">Transfer items first</span>
								<p class="text-sm text-slate-500 dark:text-slate-400">
									Move all items to another container, then delete this one
								</p>
								{#if selectedMode === 'transfer'}
									<select
										bind:value={selectedTransferContainer}
										class="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-200 dark:border-slate-600 dark:bg-slate-700 dark:focus:ring-primary-800"
										on:click|stopPropagation
									>
										<option value="">Select target container...</option>
										{#each availableContainers as container}
											<option value={container.id}>
												{'  '.repeat(container.depth)}{container.name}
											</option>
										{/each}
									</select>
								{/if}
							</div>
						</label>
					{/if}
				</div>
			{:else}
				<p class="text-sm text-slate-500 dark:text-slate-400">
					This container is empty and can be safely deleted.
				</p>
			{/if}
		</div>

		<!-- Footer -->
		<div class="flex justify-end gap-3 border-t border-slate-200 p-4 dark:border-slate-700">
			<button
				type="button"
				class="rounded-lg px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
				on:click={handleCancel}
				disabled={isDeleting}
			>
				Cancel
			</button>
			<button
				type="button"
				class="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
				on:click={handleConfirm}
				disabled={isDeleting || (selectedMode === 'transfer' && !selectedTransferContainer)}
			>
				{#if isDeleting}
					<span class="flex items-center gap-2">
						<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Deleting...
					</span>
				{:else}
					Delete Container
				{/if}
			</button>
		</div>
	</div>
</div>
