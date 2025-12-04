<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth, user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { users } from '$lib/api';
	import { UserCard, Button, Input, Modal } from '$lib/components';
	import type { User } from '$lib/types';

	let userList: User[] = [];
	let loading = true;
	let selectedUser: User | null = null;
	let password = '';
	let loggingIn = false;
	let showPasswordModal = false;

	onMount(async () => {
		if ($user) {
			goto('/');
			return;
		}

		try {
			userList = await users.listUsers();
		} finally {
			loading = false;
		}
	});

	async function handleUserClick(clickedUser: User) {
		if (clickedUser.requires_password) {
			selectedUser = clickedUser;
			showPasswordModal = true;
		} else {
			await login(clickedUser.id);
		}
	}

	async function handlePasswordSubmit() {
		if (selectedUser) {
			await login(selectedUser.id, password);
		}
	}

	async function login(userId: string, pwd?: string) {
		loggingIn = true;
		try {
			await auth.login(userId, pwd);
			goto('/');
		} catch (error) {
			toast.error('Login failed. Please check your credentials.');
		} finally {
			loggingIn = false;
			password = '';
			showPasswordModal = false;
		}
	}
</script>

<svelte:head>
	<title>Login - StorageHub</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700 px-4">
	<div class="w-full max-w-2xl">
		<!-- Logo -->
		<div class="mb-8 text-center">
			<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-primary-600 shadow-lg">
				<svg class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
				</svg>
			</div>
			<h1 class="mt-4 text-3xl font-bold text-white">StorageHub</h1>
			<p class="mt-2 text-primary-200">Who's using StorageHub?</p>
		</div>

		<!-- User Grid -->
		<div class="rounded-2xl bg-white/10 p-6 backdrop-blur">
			{#if loading}
				<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
					{#each [1, 2, 3] as _}
						<div class="h-40 animate-pulse rounded-xl bg-white/20"></div>
					{/each}
				</div>
			{:else if userList.length === 0}
				<div class="py-12 text-center">
					<svg class="mx-auto h-12 w-12 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
					</svg>
					<h3 class="mt-4 text-lg font-medium text-white">No users yet</h3>
					<p class="mt-2 text-primary-200">Create your first user to get started.</p>
				</div>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
					{#each userList as u}
						<UserCard user={u} on:click={() => handleUserClick(u)} />
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- Password Modal -->
<Modal open={showPasswordModal} title="Enter Password" on:close={() => (showPasswordModal = false)}>
	{#if selectedUser}
		<form on:submit|preventDefault={handlePasswordSubmit}>
			<p class="mb-4 text-slate-600">
				Enter the password for <strong>{selectedUser.name}</strong>
			</p>
			<Input
				type="password"
				label="Password"
				bind:value={password}
				required
				id="password"
			/>
		</form>
	{/if}

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showPasswordModal = false)}>Cancel</Button>
		<Button loading={loggingIn} on:click={handlePasswordSubmit}>Sign In</Button>
	</svelte:fragment>
</Modal>
