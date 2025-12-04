<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user, auth } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { theme, type Theme } from '$lib/stores/theme';
	import { users, activity } from '$lib/api';
	import { Card, Button, Input, Modal } from '$lib/components';
	import type { Activity, ActivityListResponse } from '$lib/api/activity';

	type Tab = 'profile' | 'activity' | 'appearance' | 'data';

	let activeTab: Tab = 'profile';
	let loading = false;
	let saving = false;

	// Profile form
	let profileName = '';
	let profileEmail = '';
	let showPasswordModal = false;
	let newPassword = '';
	let confirmPassword = '';
	let changingPassword = false;

	// Activity
	let activities: Activity[] = [];
	let activityPage = 1;
	let activityHasMore = false;
	let loadingActivity = false;

	// Data
	let exporting = false;

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		profileName = $user.name;
		profileEmail = $user.email || '';
	});

	async function handleSaveProfile() {
		if (!$user || !profileName.trim()) return;

		saving = true;
		try {
			const updated = await users.updateUser($user.id, {
				name: profileName.trim(),
				email: profileEmail.trim() || undefined
			});
			auth.updateUser(updated);
			toast.success('Profile updated');
		} catch (error) {
			toast.error('Failed to update profile');
		} finally {
			saving = false;
		}
	}

	async function handleChangePassword() {
		if (!$user || !newPassword) return;
		if (newPassword !== confirmPassword) {
			toast.error('Passwords do not match');
			return;
		}
		if (newPassword.length < 4) {
			toast.error('Password must be at least 4 characters');
			return;
		}

		changingPassword = true;
		try {
			await users.updateUser($user.id, {
				password: newPassword,
				requires_password: true
			});
			toast.success('Password changed successfully');
			showPasswordModal = false;
			newPassword = '';
			confirmPassword = '';
		} catch (error) {
			toast.error('Failed to change password');
		} finally {
			changingPassword = false;
		}
	}

	async function handleRemovePassword() {
		if (!$user) return;
		if (!confirm('Remove password protection? Anyone will be able to access your account.')) return;

		try {
			await users.updateUser($user.id, { requires_password: false });
			auth.updateUser({ ...$user, requires_password: false });
			toast.success('Password protection removed');
		} catch (error) {
			toast.error('Failed to remove password');
		}
	}

	async function loadActivities(reset = false) {
		if (reset) {
			activityPage = 1;
			activities = [];
		}

		loadingActivity = true;
		try {
			const response = await activity.getMyActivities(activityPage, 20);
			activities = [...activities, ...response.items];
			activityHasMore = response.has_more;
		} catch (error) {
			toast.error('Failed to load activity');
		} finally {
			loadingActivity = false;
		}
	}

	function loadMoreActivities() {
		activityPage++;
		loadActivities();
	}

	function setTheme(newTheme: Theme) {
		theme.set(newTheme);
		toast.success(`Theme set to ${newTheme}`);
	}

	async function exportJson() {
		exporting = true;
		try {
			window.open('/api/export/json', '_blank');
			toast.success('Export started');
		} catch (error) {
			toast.error('Export failed');
		} finally {
			exporting = false;
		}
	}

	async function exportCsv() {
		exporting = true;
		try {
			window.open('/api/export/csv', '_blank');
			toast.success('Export started');
		} catch (error) {
			toast.error('Export failed');
		} finally {
			exporting = false;
		}
	}

	function formatActivityTime(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const minutes = Math.floor(diff / 60000);
		const hours = Math.floor(diff / 3600000);
		const days = Math.floor(diff / 86400000);

		if (minutes < 1) return 'Just now';
		if (minutes < 60) return `${minutes}m ago`;
		if (hours < 24) return `${hours}h ago`;
		if (days < 7) return `${days}d ago`;
		return date.toLocaleDateString();
	}

	function getActionColor(action: string): string {
		switch (action) {
			case 'created':
				return 'bg-green-100 text-green-700';
			case 'updated':
				return 'bg-blue-100 text-blue-700';
			case 'moved':
				return 'bg-purple-100 text-purple-700';
			case 'deleted':
				return 'bg-red-100 text-red-700';
			default:
				return 'bg-slate-100 text-slate-700';
		}
	}

	function getEntityLink(entityType: string, entityId: string): string | null {
		switch (entityType) {
			case 'item':
				return `/items/${entityId}`;
			case 'container':
				return `/containers/${entityId}`;
			case 'location':
				return `/locations/${entityId}`;
			default:
				return null;
		}
	}

	// Load activities when switching to activity tab
	$: if (activeTab === 'activity' && activities.length === 0) {
		loadActivities(true);
	}
</script>

<svelte:head>
	<title>Settings - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Settings</h1>
		<p class="mt-1 text-slate-500 dark:text-slate-400">Manage your account and preferences</p>
	</div>

	<!-- Tabs -->
	<div class="border-b border-slate-200 dark:border-slate-700">
		<nav class="-mb-px flex gap-6">
			{#each [
				{ id: 'profile', label: 'Profile' },
				{ id: 'activity', label: 'Activity' },
				{ id: 'appearance', label: 'Appearance' },
				{ id: 'data', label: 'Data' }
			] as tab}
				<button
					class="border-b-2 pb-3 text-sm font-medium transition-colors {activeTab === tab.id
						? 'border-primary-500 text-primary-600'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400'}"
					on:click={() => (activeTab = tab.id as Tab)}
				>
					{tab.label}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Profile Tab -->
	{#if activeTab === 'profile'}
		<Card>
			<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-white">Profile Information</h2>
			<form on:submit|preventDefault={handleSaveProfile} class="space-y-4">
				<Input label="Name" bind:value={profileName} required id="profile-name" />
				<Input label="Email" type="email" bind:value={profileEmail} placeholder="Optional" id="profile-email" />

				<div class="flex justify-end">
					<Button type="submit" loading={saving}>Save Changes</Button>
				</div>
			</form>
		</Card>

		<Card>
			<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Password</h2>
			{#if $user?.requires_password}
				<p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
					Your account is protected with a password.
				</p>
				<div class="flex gap-2">
					<Button variant="secondary" on:click={() => (showPasswordModal = true)}>
						Change Password
					</Button>
					<Button variant="secondary" on:click={handleRemovePassword}>Remove Password</Button>
				</div>
			{:else}
				<p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
					Your account does not require a password. Anyone can sign in as you.
				</p>
				<Button on:click={() => (showPasswordModal = true)}>Set Password</Button>
			{/if}
		</Card>

		<Card>
			<h2 class="mb-4 text-lg font-semibold text-red-600">Danger Zone</h2>
			<p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
				Sign out from your current session.
			</p>
			<Button variant="secondary" on:click={() => auth.logout()}>Sign Out</Button>
		</Card>
	{/if}

	<!-- Activity Tab -->
	{#if activeTab === 'activity'}
		<Card>
			<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-white">Recent Activity</h2>

			{#if loadingActivity && activities.length === 0}
				<div class="space-y-4">
					{#each [1, 2, 3, 4, 5] as _}
						<div class="h-16 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800"></div>
					{/each}
				</div>
			{:else if activities.length === 0}
				<p class="py-8 text-center text-slate-500 dark:text-slate-400">No activity yet</p>
			{:else}
				<div class="space-y-3">
					{#each activities as act}
						{@const link = getEntityLink(act.entity_type, act.entity_id)}
						<div class="flex items-start gap-4 rounded-lg border border-slate-100 p-4 dark:border-slate-700">
							<span
								class="inline-flex rounded-full px-2 py-1 text-xs font-medium capitalize {getActionColor(
									act.action
								)}"
							>
								{act.action}
							</span>
							<div class="flex-1 min-w-0">
								{#if link}
									<a href={link} class="font-medium text-slate-900 hover:text-primary-600 dark:text-white">
										{act.entity_name}
									</a>
								{:else}
									<span class="font-medium text-slate-900 dark:text-white">{act.entity_name}</span>
								{/if}
								<p class="text-sm text-slate-500 dark:text-slate-400">
									{act.entity_type}
									{#if act.details}
										{#if act.action === 'moved'}
											- moved from {act.details.from} to {act.details.to}
										{/if}
									{/if}
								</p>
							</div>
							<span class="text-xs text-slate-400">{formatActivityTime(act.created_at)}</span>
						</div>
					{/each}
				</div>

				{#if activityHasMore}
					<div class="mt-4 text-center">
						<Button variant="secondary" on:click={loadMoreActivities} loading={loadingActivity}>
							Load More
						</Button>
					</div>
				{/if}
			{/if}
		</Card>
	{/if}

	<!-- Appearance Tab -->
	{#if activeTab === 'appearance'}
		<Card>
			<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-white">Theme</h2>
			<div class="grid gap-4 sm:grid-cols-3">
				{#each [
					{ id: 'light', label: 'Light', icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z' },
					{ id: 'dark', label: 'Dark', icon: 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z' },
					{ id: 'system', label: 'System', icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' }
				] as option}
					<button
						class="flex flex-col items-center gap-3 rounded-xl border-2 p-6 transition-all {$theme === option.id
							? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
							: 'border-slate-200 hover:border-slate-300 dark:border-slate-700'}"
						on:click={() => setTheme(option.id as Theme)}
					>
						<svg class="h-8 w-8 {$theme === option.id ? 'text-primary-600' : 'text-slate-400'}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={option.icon} />
						</svg>
						<span class="text-sm font-medium {$theme === option.id ? 'text-primary-600' : 'text-slate-700 dark:text-slate-300'}">
							{option.label}
						</span>
					</button>
				{/each}
			</div>
		</Card>
	{/if}

	<!-- Data Tab -->
	{#if activeTab === 'data'}
		<Card>
			<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-white">Export Data</h2>
			<p class="mb-6 text-sm text-slate-500 dark:text-slate-400">
				Download all your data including locations, containers, items, and tags.
			</p>

			<div class="grid gap-4 sm:grid-cols-2">
				<button
					class="flex flex-col items-center gap-3 rounded-xl border border-slate-200 p-6 transition-all hover:border-primary-300 hover:bg-primary-50 dark:border-slate-700 dark:hover:bg-primary-900/10"
					on:click={exportJson}
					disabled={exporting}
				>
					<svg class="h-10 w-10 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
						/>
					</svg>
					<div class="text-center">
						<p class="font-medium text-slate-900 dark:text-white">Export as JSON</p>
						<p class="text-sm text-slate-500 dark:text-slate-400">Full data export with all details</p>
					</div>
				</button>

				<button
					class="flex flex-col items-center gap-3 rounded-xl border border-slate-200 p-6 transition-all hover:border-primary-300 hover:bg-primary-50 dark:border-slate-700 dark:hover:bg-primary-900/10"
					on:click={exportCsv}
					disabled={exporting}
				>
					<svg class="h-10 w-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
					<div class="text-center">
						<p class="font-medium text-slate-900 dark:text-white">Export as CSV</p>
						<p class="text-sm text-slate-500 dark:text-slate-400">Items list for spreadsheets</p>
					</div>
				</button>
			</div>
		</Card>

		<Card>
			<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Storage Statistics</h2>
			<div class="grid gap-4 sm:grid-cols-4">
				<div class="rounded-lg bg-slate-50 p-4 text-center dark:bg-slate-800">
					<p class="text-2xl font-bold text-slate-900 dark:text-white">-</p>
					<p class="text-sm text-slate-500 dark:text-slate-400">Locations</p>
				</div>
				<div class="rounded-lg bg-slate-50 p-4 text-center dark:bg-slate-800">
					<p class="text-2xl font-bold text-slate-900 dark:text-white">-</p>
					<p class="text-sm text-slate-500 dark:text-slate-400">Containers</p>
				</div>
				<div class="rounded-lg bg-slate-50 p-4 text-center dark:bg-slate-800">
					<p class="text-2xl font-bold text-slate-900 dark:text-white">-</p>
					<p class="text-sm text-slate-500 dark:text-slate-400">Items</p>
				</div>
				<div class="rounded-lg bg-slate-50 p-4 text-center dark:bg-slate-800">
					<p class="text-2xl font-bold text-slate-900 dark:text-white">-</p>
					<p class="text-sm text-slate-500 dark:text-slate-400">Images</p>
				</div>
			</div>
		</Card>
	{/if}
</div>

<!-- Password Modal -->
<Modal
	open={showPasswordModal}
	title={$user?.requires_password ? 'Change Password' : 'Set Password'}
	on:close={() => {
		showPasswordModal = false;
		newPassword = '';
		confirmPassword = '';
	}}
>
	<form on:submit|preventDefault={handleChangePassword} class="space-y-4">
		<Input
			label="New Password"
			type="password"
			bind:value={newPassword}
			required
			id="new-password"
			placeholder="At least 4 characters"
		/>
		<Input
			label="Confirm Password"
			type="password"
			bind:value={confirmPassword}
			required
			id="confirm-password"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button
			variant="secondary"
			on:click={() => {
				showPasswordModal = false;
				newPassword = '';
				confirmPassword = '';
			}}
		>
			Cancel
		</Button>
		<Button loading={changingPassword} on:click={handleChangePassword}>
			{$user?.requires_password ? 'Change Password' : 'Set Password'}
		</Button>
	</svelte:fragment>
</Modal>
