<script lang="ts">
	export let value: string | number = '';
	export let type: 'text' | 'email' | 'password' | 'number' | 'search' = 'text';
	export let placeholder = '';
	export let label = '';
	export let id = '';
	export let required = false;
	export let disabled = false;
	export let error = '';

	function handleInput(e: Event) {
		const target = e.target as HTMLInputElement;
		value = type === 'number' ? target.valueAsNumber : target.value;
	}
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

	{#if type === 'password'}
		<input
			{id}
			type="password"
			{placeholder}
			{required}
			{disabled}
			{value}
			on:input={handleInput}
			class="input {error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}"
			on:blur
			on:focus
		/>
	{:else if type === 'email'}
		<input
			{id}
			type="email"
			{placeholder}
			{required}
			{disabled}
			{value}
			on:input={handleInput}
			class="input {error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}"
			on:blur
			on:focus
		/>
	{:else if type === 'number'}
		<input
			{id}
			type="number"
			{placeholder}
			{required}
			{disabled}
			{value}
			on:input={handleInput}
			class="input {error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}"
			on:blur
			on:focus
		/>
	{:else if type === 'search'}
		<input
			{id}
			type="search"
			{placeholder}
			{required}
			{disabled}
			{value}
			on:input={handleInput}
			class="input {error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}"
			on:blur
			on:focus
		/>
	{:else}
		<input
			{id}
			type="text"
			{placeholder}
			{required}
			{disabled}
			{value}
			on:input={handleInput}
			class="input {error ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : ''}"
			on:blur
			on:focus
		/>
	{/if}

	{#if error}
		<p class="mt-1 text-sm text-red-500">{error}</p>
	{/if}
</div>
