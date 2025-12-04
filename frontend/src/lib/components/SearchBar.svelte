<script lang="ts">
	import { goto } from '$app/navigation';

	export let value = '';
	export let placeholder = 'Search items...';

	function handleSubmit() {
		if (value.trim()) {
			goto(`/search?q=${encodeURIComponent(value.trim())}`);
		}
	}
</script>

<form on:submit|preventDefault={handleSubmit} class="relative w-full max-w-md">
	<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
		<svg class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
			/>
		</svg>
	</div>
	<input
		type="search"
		bind:value
		{placeholder}
		class="input pl-10"
	/>
</form>
