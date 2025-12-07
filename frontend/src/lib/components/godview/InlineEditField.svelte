<script lang="ts">
	import { createEventDispatcher, tick } from 'svelte';

	export let value: string;
	export let placeholder = '';
	export let className = '';

	const dispatch = createEventDispatcher<{ save: string }>();

	let editing = false;
	let editValue = value;
	let saving = false;
	let success = false;
	let inputEl: HTMLInputElement;

	async function startEdit() {
		editing = true;
		editValue = value || '';
		await tick();
		inputEl?.focus();
		inputEl?.select();
	}

	async function save() {
		if (editValue === value) {
			editing = false;
			return;
		}
		saving = true;
		dispatch('save', editValue);
		// Parent will update value, then we close editing
		editing = false;
		saving = false;
		// Show success flash
		success = true;
		setTimeout(() => (success = false), 500);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			save();
		}
		if (e.key === 'Escape') {
			editing = false;
			editValue = value || '';
		}
	}

	function handleBlur() {
		// Small delay to allow click events to fire first
		setTimeout(() => {
			if (editing) save();
		}, 100);
	}

	// Sync value when parent updates
	$: if (!editing) editValue = value || '';
</script>

{#if editing}
	<input
		bind:this={inputEl}
		bind:value={editValue}
		on:blur={handleBlur}
		on:keydown={handleKeydown}
		class="w-full rounded border border-primary-400 bg-white px-2 py-1 text-sm outline-none ring-2 ring-primary-200 dark:border-primary-600 dark:bg-slate-800 dark:ring-primary-800 {className}"
		{placeholder}
		disabled={saving}
	/>
{:else}
	<button
		class="w-full truncate rounded px-2 py-1 text-left text-sm transition-colors
			hover:bg-slate-100 dark:hover:bg-slate-700
			{!value ? 'italic text-slate-400' : 'text-slate-900 dark:text-white'}
			{success ? 'bg-green-100 dark:bg-green-900/30' : ''}
			{className}"
		on:click={startEdit}
		title="Click to edit"
	>
		{value || placeholder || '—'}
	</button>
{/if}
