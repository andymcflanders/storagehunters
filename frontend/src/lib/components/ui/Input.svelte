<script lang="ts">
	export let value = '';
	export let type: 'text' | 'email' | 'password' | 'number' | 'search' = 'text';
	export let placeholder = '';
	export let label = '';
	export let id = '';
	export let required = false;
	export let disabled = false;
	export let error = '';
</script>

<div class="w-full">
	{#if label}
		<label for={id} class="label">
			{label}
			{#if required}
				<span class="text-red-500">*</span>
			{/if}
		</label>
	{/if}

	<input
		{id}
		{type}
		{placeholder}
		{required}
		{disabled}
		bind:value
		class="input {error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}"
		on:input
		on:blur
		on:focus
	/>

	{#if error}
		<p class="mt-1 text-sm text-red-500">{error}</p>
	{/if}
</div>
