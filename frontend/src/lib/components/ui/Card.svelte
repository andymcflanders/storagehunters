<script lang="ts">
	export let hover = false;
	export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';

	const paddings = {
		none: '',
		sm: 'p-4',
		md: 'p-6',
		lg: 'p-8'
	};
</script>

<div
	class="rounded-xl bg-white dark:bg-slate-800 shadow-sm ring-1 ring-slate-900/5 dark:ring-slate-700/50 {paddings[padding]} {hover
		? 'transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md'
		: ''}"
>
	<slot />
</div>
