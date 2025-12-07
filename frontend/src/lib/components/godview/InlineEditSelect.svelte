<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let value: string;
	export let options: { value: string; label: string; color?: string }[];
	export let className = '';

	const dispatch = createEventDispatcher<{ change: string }>();

	let success = false;

	function handleChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const newValue = target.value;
		if (newValue !== value) {
			dispatch('change', newValue);
			// Show success flash
			success = true;
			setTimeout(() => (success = false), 500);
		}
	}

	function getOptionColor(optionValue: string): string {
		const option = options.find((o) => o.value === optionValue);
		return option?.color || '';
	}
</script>

<select
	{value}
	on:change={handleChange}
	class="cursor-pointer rounded border-0 bg-transparent px-1 py-0.5 text-sm font-medium outline-none
		hover:bg-slate-100 focus:ring-2 focus:ring-primary-200 dark:hover:bg-slate-700 dark:focus:ring-primary-800
		{success ? 'bg-green-100 dark:bg-green-900/30' : ''}
		{getOptionColor(value)}
		{className}"
>
	{#each options as option}
		<option value={option.value}>{option.label}</option>
	{/each}
</select>
