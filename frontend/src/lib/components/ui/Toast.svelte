<script lang="ts">
	import { fly } from 'svelte/transition';
	import { toast, type Toast } from '$lib/stores/toast';

	const icons = {
		success: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />`,
		error: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />`,
		warning: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />`,
		info: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`
	};

	const colors = {
		success: 'bg-green-50 text-green-800 border-green-200',
		error: 'bg-red-50 text-red-800 border-red-200',
		warning: 'bg-amber-50 text-amber-800 border-amber-200',
		info: 'bg-blue-50 text-blue-800 border-blue-200'
	};

	const iconColors = {
		success: 'text-green-500',
		error: 'text-red-500',
		warning: 'text-amber-500',
		info: 'text-blue-500'
	};
</script>

<div class="fixed right-4 top-4 z-50 flex flex-col gap-2">
	{#each $toast as t (t.id)}
		<div
			class="flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg {colors[t.type]}"
			in:fly={{ x: 100, duration: 300 }}
			out:fly={{ x: 100, duration: 200 }}
		>
			<svg class="h-5 w-5 {iconColors[t.type]}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				{@html icons[t.type]}
			</svg>
			<p class="flex-1 text-sm font-medium">{t.message}</p>
			<button
				type="button"
				class="rounded p-1 opacity-70 hover:opacity-100"
				on:click={() => toast.remove(t.id)}
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
	{/each}
</div>
