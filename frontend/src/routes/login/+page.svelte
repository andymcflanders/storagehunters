<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { _ } from '$lib/i18n';
	import { auth, user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { users } from '$lib/api';
	import { UserCard, Button, Input, Modal } from '$lib/components';
	import type { PublicUser } from '$lib/types';

	let userList: PublicUser[] = [];
	let loading = true;
	let selectedUser: PublicUser | null = null;
	let password = '';
	let loggingIn = false;
	let showPasswordModal = false;

	// Admin sign-in modal state — separate flow because admins are
	// excluded from the household card grid by design.
	let showAdminModal = false;
	let adminEmail = '';
	let adminPassword = '';

	onMount(async () => {
		if ($user) {
			goto('/');
			return;
		}

		try {
			// Hide admins from the household grid; they sign in via the
			// dedicated email + password modal below. Profile users (e.g.
			// small kids) own items but never log in, so hide them too.
			userList = await users.listUsers({ includeAdmins: false, includeProfiles: false });
		} finally {
			loading = false;
		}
	});

	async function handleUserClick(clickedUser: PublicUser) {
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

	async function handleAdminLogin() {
		if (!adminEmail.trim() || !adminPassword) return;
		loggingIn = true;
		try {
			await auth.loginByEmail(adminEmail.trim(), adminPassword);
			goto('/');
		} catch {
			toast.error('Login failed. Please check your credentials.');
		} finally {
			loggingIn = false;
			adminPassword = '';
			showAdminModal = false;
		}
	}
</script>

<svelte:head>
	<title>{$_('auth.signIn')} - {$_('app.name')}</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700 px-4">
	<div class="w-full max-w-2xl">
		<!-- Logo -->
		<div class="mb-8 text-center">
			<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white dark:bg-slate-800 text-primary-600 dark:text-primary-400 shadow-lg">
				<svg class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
				</svg>
			</div>
			<h1 class="mt-4 text-3xl font-bold text-white">{$_('app.name')}</h1>
			<p class="mt-2 text-primary-200">{$_('auth.selectUser')}</p>
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
					<h3 class="mt-4 text-lg font-medium text-white">{$_('auth.noUsersYet')}</h3>
					<p class="mt-2 text-primary-200">{$_('auth.createFirstUser')}</p>
				</div>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
					{#each userList as u}
						<UserCard user={u} on:click={() => handleUserClick(u)} />
					{/each}
				</div>
			{/if}
		</div>

		<!-- Admin sign-in entry point. Deliberately understated — most
		     visitors are household users tapping their card; admins are
		     the rare case who arrive here knowing they need the link. -->
		<div class="mt-6 text-center">
			<button
				class="text-sm text-primary-100/80 underline-offset-4 hover:text-white hover:underline"
				on:click={() => (showAdminModal = true)}
			>
				{$_('auth.adminSignInLink')}
			</button>
		</div>
	</div>
</div>

<!-- Household password modal -->
<Modal open={showPasswordModal} title={$_('auth.enterPassword')} on:close={() => (showPasswordModal = false)}>
	{#if selectedUser}
		<form on:submit|preventDefault={handlePasswordSubmit}>
			<p class="mb-4 text-slate-600 dark:text-slate-400">
				{$_('auth.signInAs')} <strong>{selectedUser.name}</strong>
			</p>
			<Input
				type="password"
				label={$_('auth.password')}
				bind:value={password}
				required
				id="password"
			/>
		</form>
	{/if}

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showPasswordModal = false)}>{$_('common.cancel')}</Button>
		<Button loading={loggingIn} on:click={handlePasswordSubmit}>{$_('auth.signIn')}</Button>
	</svelte:fragment>
</Modal>

<!-- Admin sign-in modal -->
<Modal open={showAdminModal} title={$_('auth.adminSignInTitle')} on:close={() => (showAdminModal = false)}>
	<form on:submit|preventDefault={handleAdminLogin} class="space-y-4">
		<p class="text-sm text-slate-600 dark:text-slate-300">{$_('auth.adminSignInIntro')}</p>
		<Input
			type="email"
			label={$_('auth.email')}
			bind:value={adminEmail}
			required
			id="admin-login-email"
		/>
		<Input
			type="password"
			label={$_('auth.password')}
			bind:value={adminPassword}
			required
			id="admin-login-password"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showAdminModal = false)}>{$_('common.cancel')}</Button>
		<Button loading={loggingIn} on:click={handleAdminLogin} disabled={!adminEmail.trim() || !adminPassword}>
			{$_('auth.signIn')}
		</Button>
	</svelte:fragment>
</Modal>
