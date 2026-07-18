<script lang="ts">
	import type { PublicUser } from '$lib/types';

	export let user: PublicUser;
	export let selected = false;
</script>

<button
	class="group flex w-full flex-col items-center gap-3 rounded-xl bg-white dark:bg-slate-800 p-6 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md {selected
		? 'ring-2 ring-primary-500'
		: ''}"
	on:click
>
	<!-- Avatar -->
	<div
		class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-primary-400 to-primary-600 text-3xl font-bold text-white"
	>
		{#if user.avatar_url}
			<img src={user.avatar_url} alt={user.name} class="h-full w-full rounded-full object-cover" />
		{:else}
			{user.name.charAt(0).toUpperCase()}
		{/if}
	</div>

	<!-- Name -->
	<span class="text-lg font-medium text-slate-900 dark:text-white">{user.name}</span>

	<!-- Password indicator -->
	{#if user.requires_password}
		<div class="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
			<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
				/>
			</svg>
			<span>Password protected</span>
		</div>
	{/if}
</button>
