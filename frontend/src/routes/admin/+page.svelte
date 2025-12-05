<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { admin } from '$lib/api';
	import { Card, Button } from '$lib/components';
	import type { SystemStats, AdminUser, ActivityLogItem } from '$lib/api/admin';

	type Tab = 'dashboard' | 'users' | 'activity';

	let activeTab: Tab = 'dashboard';
	let stats: SystemStats | null = null;
	let users: AdminUser[] = [];
	let usersTotal = 0;
	let usersPage = 1;
	let activityLogs: ActivityLogItem[] = [];
	let activityTotal = 0;
	let activityPage = 1;
	let loading = true;
	let loadingUsers = false;
	let loadingActivity = false;

	// User modal state
	let showUserModal = false;
	let editingUser: AdminUser | null = null;
	let userFormData = {
		name: '',
		email: '',
		role: 'user' as 'admin' | 'user',
		requires_password: false,
		password: '',
		is_active: true
	};
	let savingUser = false;

	// Filters
	let userSearch = '';
	let userRoleFilter = '';
	let userActiveFilter = '';

	const tabs: { id: Tab; label: string; icon: string }[] = [
		{ id: 'dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
		{ id: 'users', label: 'Users', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
		{ id: 'activity', label: 'Activity Logs', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' }
	];

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		// Check if user is admin
		if ($user.role !== 'admin') {
			toast.error('Admin access required');
			goto('/');
			return;
		}

		await loadStats();
	});

	async function loadStats() {
		loading = true;
		try {
			stats = await admin.getSystemStats();
		} catch (error) {
			toast.error('Failed to load stats');
		} finally {
			loading = false;
		}
	}

	async function loadUsers() {
		loadingUsers = true;
		try {
			const filters: admin.UserListFilters = {
				page: usersPage,
				page_size: 20,
				search: userSearch || undefined,
				role: userRoleFilter as 'admin' | 'user' || undefined,
				is_active: userActiveFilter === '' ? undefined : userActiveFilter === 'true'
			};
			const response = await admin.listUsers(filters);
			users = response.items;
			usersTotal = response.total;
		} catch (error) {
			toast.error('Failed to load users');
		} finally {
			loadingUsers = false;
		}
	}

	async function loadActivity() {
		loadingActivity = true;
		try {
			const response = await admin.getActivityLogs({
				page: activityPage,
				page_size: 50,
				days: 30
			});
			activityLogs = response.items;
			activityTotal = response.total;
		} catch (error) {
			toast.error('Failed to load activity logs');
		} finally {
			loadingActivity = false;
		}
	}

	function setActiveTab(tabId: string) {
		activeTab = tabId as Tab;
		if (tabId === 'users' && users.length === 0) {
			loadUsers();
		} else if (tabId === 'activity' && activityLogs.length === 0) {
			loadActivity();
		}
	}

	function openCreateUserModal() {
		editingUser = null;
		userFormData = {
			name: '',
			email: '',
			role: 'user',
			requires_password: false,
			password: '',
			is_active: true
		};
		showUserModal = true;
	}

	function openEditUserModal(u: AdminUser) {
		editingUser = u;
		userFormData = {
			name: u.name,
			email: u.email || '',
			role: u.role,
			requires_password: u.requires_password,
			password: '',
			is_active: u.is_active
		};
		showUserModal = true;
	}

	async function handleSaveUser() {
		if (!userFormData.name.trim()) {
			toast.warning('Please enter a name');
			return;
		}

		savingUser = true;
		try {
			if (editingUser) {
				const updateData: admin.UpdateUserRequest = {
					name: userFormData.name,
					email: userFormData.email || null,
					role: userFormData.role,
					requires_password: userFormData.requires_password,
					is_active: userFormData.is_active
				};
				if (userFormData.password) {
					updateData.password = userFormData.password;
				}
				await admin.updateUser(editingUser.id, updateData);
				toast.success('User updated');
			} else {
				await admin.createUser({
					name: userFormData.name,
					email: userFormData.email || null,
					role: userFormData.role,
					requires_password: userFormData.requires_password,
					password: userFormData.password || null
				});
				toast.success('User created');
			}
			showUserModal = false;
			await loadUsers();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to save user';
			toast.error(message);
		} finally {
			savingUser = false;
		}
	}

	async function handleDeleteUser(u: AdminUser) {
		if (!confirm(`Delete user "${u.name}"? This cannot be undone.`)) return;

		try {
			await admin.deleteUser(u.id);
			toast.success('User deleted');
			await loadUsers();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to delete user';
			toast.error(message);
		}
	}

	async function handleToggleUserActive(u: AdminUser) {
		try {
			await admin.updateUser(u.id, { is_active: !u.is_active });
			toast.success(u.is_active ? 'User deactivated' : 'User activated');
			await loadUsers();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to update user';
			toast.error(message);
		}
	}

	function handleSearchUsers() {
		usersPage = 1;
		loadUsers();
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatDateTime(dateStr: string): string {
		return new Date(dateStr).toLocaleString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getActionColor(action: string): string {
		switch (action) {
			case 'created':
				return 'bg-green-100 text-green-800';
			case 'updated':
				return 'bg-blue-100 text-blue-800';
			case 'deleted':
				return 'bg-red-100 text-red-800';
			case 'moved':
				return 'bg-yellow-100 text-yellow-800';
			default:
				return 'bg-slate-100 text-slate-800';
		}
	}
</script>

<svelte:head>
	<title>Admin Panel - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-2xl font-bold text-slate-900">Admin Panel</h1>
		<p class="mt-1 text-slate-500">Manage users, view system stats, and monitor activity</p>
	</div>

	<!-- Tabs -->
	<div class="border-b border-slate-200">
		<nav class="-mb-px flex space-x-8">
			{#each tabs as tab}
				<button
					class="flex items-center gap-2 border-b-2 px-1 py-4 text-sm font-medium transition-colors
						{activeTab === tab.id
						? 'border-primary-500 text-primary-600'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'}"
					on:click={() => setActiveTab(tab.id)}
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={tab.icon} />
					</svg>
					{tab.label}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Dashboard Tab -->
	{#if activeTab === 'dashboard'}
		{#if loading}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				{#each [1, 2, 3, 4] as _}
					<div class="h-24 animate-pulse rounded-xl bg-slate-200"></div>
				{/each}
			</div>
		{:else if stats}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<!-- Users Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500">Total Users</p>
							<p class="text-2xl font-bold text-slate-900">{stats.total_users}</p>
							<p class="text-xs text-slate-400">{stats.active_users} active, {stats.admin_users} admins</p>
						</div>
					</div>
				</Card>

				<!-- Locations Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 text-green-600">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500">Locations</p>
							<p class="text-2xl font-bold text-slate-900">{stats.total_locations}</p>
						</div>
					</div>
				</Card>

				<!-- Containers Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500">Containers</p>
							<p class="text-2xl font-bold text-slate-900">{stats.total_containers}</p>
						</div>
					</div>
				</Card>

				<!-- Items Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500">Items</p>
							<p class="text-2xl font-bold text-slate-900">{stats.total_items}</p>
							<p class="text-xs text-slate-400">+{stats.items_created_last_30_days} last 30 days</p>
						</div>
					</div>
				</Card>
			</div>

			<!-- Activity Summary -->
			<Card>
				<h3 class="text-lg font-semibold text-slate-900">Recent Activity</h3>
				<p class="mt-1 text-sm text-slate-500">
					{stats.recent_activity_count} actions in the last 30 days
				</p>
				<div class="mt-4">
					<Button variant="secondary" on:click={() => setActiveTab('activity')}>
						View All Activity
					</Button>
				</div>
			</Card>
		{/if}
	{/if}

	<!-- Users Tab -->
	{#if activeTab === 'users'}
		<div class="space-y-4">
			<!-- Toolbar -->
			<div class="flex flex-wrap items-center gap-4">
				<div class="flex-1">
					<form on:submit|preventDefault={handleSearchUsers} class="flex gap-2">
						<input
							type="text"
							bind:value={userSearch}
							placeholder="Search users..."
							class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
						/>
						<Button type="submit" variant="secondary">Search</Button>
					</form>
				</div>
				<select
					bind:value={userRoleFilter}
					on:change={() => { usersPage = 1; loadUsers(); }}
					class="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				>
					<option value="">All Roles</option>
					<option value="admin">Admin</option>
					<option value="user">User</option>
				</select>
				<select
					bind:value={userActiveFilter}
					on:change={() => { usersPage = 1; loadUsers(); }}
					class="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				>
					<option value="">All Status</option>
					<option value="true">Active</option>
					<option value="false">Inactive</option>
				</select>
				<Button on:click={openCreateUserModal}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add User
				</Button>
			</div>

			<!-- Users Table -->
			{#if loadingUsers}
				<div class="animate-pulse space-y-2">
					{#each [1, 2, 3, 4, 5] as _}
						<div class="h-16 rounded-lg bg-slate-200"></div>
					{/each}
				</div>
			{:else}
				<Card>
					<div class="overflow-x-auto">
						<table class="w-full">
							<thead>
								<tr class="border-b border-slate-200 text-left text-sm text-slate-500">
									<th class="pb-3 font-medium">User</th>
									<th class="pb-3 font-medium">Role</th>
									<th class="pb-3 font-medium">Status</th>
									<th class="pb-3 font-medium">Items</th>
									<th class="pb-3 font-medium">Created</th>
									<th class="pb-3 font-medium">Last Active</th>
									<th class="pb-3 font-medium">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-100">
								{#each users as u}
									<tr class="text-sm">
										<td class="py-3">
											<div>
												<p class="font-medium text-slate-900">{u.name}</p>
												<p class="text-slate-500">{u.email || 'No email'}</p>
											</div>
										</td>
										<td class="py-3">
											<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
												{u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 text-slate-800'}">
												{u.role}
											</span>
										</td>
										<td class="py-3">
											<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
												{u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
												{u.is_active ? 'Active' : 'Inactive'}
											</span>
										</td>
										<td class="py-3 text-slate-600">{u.item_count}</td>
										<td class="py-3 text-slate-600">{formatDate(u.created_at)}</td>
										<td class="py-3 text-slate-600">
											{u.last_activity ? formatDate(u.last_activity) : 'Never'}
										</td>
										<td class="py-3">
											<div class="flex items-center gap-1">
												<button
													class="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
													title="Edit"
													on:click={() => openEditUserModal(u)}
												>
													<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
													</svg>
												</button>
												<button
													class="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
													title={u.is_active ? 'Deactivate' : 'Activate'}
													on:click={() => handleToggleUserActive(u)}
												>
													{#if u.is_active}
														<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
														</svg>
													{:else}
														<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
														</svg>
													{/if}
												</button>
												<button
													class="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
													title="Delete"
													on:click={() => handleDeleteUser(u)}
												>
													<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
												</button>
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>

					{#if users.length === 0}
						<div class="py-8 text-center text-slate-500">No users found</div>
					{/if}

					<!-- Pagination -->
					{#if usersTotal > 20}
						<div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
							<p class="text-sm text-slate-500">
								Showing {(usersPage - 1) * 20 + 1} to {Math.min(usersPage * 20, usersTotal)} of {usersTotal} users
							</p>
							<div class="flex gap-2">
								<Button
									variant="secondary"
									size="sm"
									disabled={usersPage === 1}
									on:click={() => { usersPage--; loadUsers(); }}
								>
									Previous
								</Button>
								<Button
									variant="secondary"
									size="sm"
									disabled={usersPage * 20 >= usersTotal}
									on:click={() => { usersPage++; loadUsers(); }}
								>
									Next
								</Button>
							</div>
						</div>
					{/if}
				</Card>
			{/if}
		</div>
	{/if}

	<!-- Activity Tab -->
	{#if activeTab === 'activity'}
		<div class="space-y-4">
			{#if loadingActivity}
				<div class="animate-pulse space-y-2">
					{#each [1, 2, 3, 4, 5] as _}
						<div class="h-16 rounded-lg bg-slate-200"></div>
					{/each}
				</div>
			{:else}
				<Card>
					<div class="space-y-4">
						{#each activityLogs as log}
							<div class="flex items-start gap-4 border-b border-slate-100 pb-4 last:border-0 last:pb-0">
								<div class="flex-1">
									<div class="flex items-center gap-2">
										<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getActionColor(log.action)}">
											{log.action}
										</span>
										<span class="text-sm font-medium text-slate-900">{log.entity_name}</span>
										<span class="text-sm text-slate-500">({log.entity_type})</span>
									</div>
									<p class="mt-1 text-sm text-slate-500">
										by {log.user_name || 'Unknown'} at {formatDateTime(log.created_at)}
									</p>
								</div>
							</div>
						{/each}

						{#if activityLogs.length === 0}
							<div class="py-8 text-center text-slate-500">No activity logs found</div>
						{/if}
					</div>

					<!-- Pagination -->
					{#if activityTotal > 50}
						<div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
							<p class="text-sm text-slate-500">
								Showing {(activityPage - 1) * 50 + 1} to {Math.min(activityPage * 50, activityTotal)} of {activityTotal} logs
							</p>
							<div class="flex gap-2">
								<Button
									variant="secondary"
									size="sm"
									disabled={activityPage === 1}
									on:click={() => { activityPage--; loadActivity(); }}
								>
									Previous
								</Button>
								<Button
									variant="secondary"
									size="sm"
									disabled={activityPage * 50 >= activityTotal}
									on:click={() => { activityPage++; loadActivity(); }}
								>
									Next
								</Button>
							</div>
						</div>
					{/if}
				</Card>
			{/if}
		</div>
	{/if}
</div>

<!-- User Modal -->
{#if showUserModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
			<h2 class="text-xl font-bold text-slate-900">
				{editingUser ? 'Edit User' : 'Create User'}
			</h2>

			<form on:submit|preventDefault={handleSaveUser} class="mt-4 space-y-4">
				<div>
					<label for="user-name" class="mb-1.5 block text-sm font-medium text-slate-700">Name</label>
					<input
						id="user-name"
						type="text"
						bind:value={userFormData.name}
						required
						class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
					/>
				</div>

				<div>
					<label for="user-email" class="mb-1.5 block text-sm font-medium text-slate-700">Email (optional)</label>
					<input
						id="user-email"
						type="email"
						bind:value={userFormData.email}
						class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
					/>
				</div>

				<div>
					<label for="user-role" class="mb-1.5 block text-sm font-medium text-slate-700">Role</label>
					<select
						id="user-role"
						bind:value={userFormData.role}
						class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
					>
						<option value="user">User</option>
						<option value="admin">Admin</option>
					</select>
				</div>

				<div>
					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							bind:checked={userFormData.requires_password}
							class="h-4 w-4 rounded border-slate-300 text-primary-600"
						/>
						<span class="text-sm text-slate-700">Require password to login</span>
					</label>
				</div>

				{#if userFormData.requires_password}
					<div>
						<label for="user-password" class="mb-1.5 block text-sm font-medium text-slate-700">
							{editingUser ? 'New Password (leave blank to keep current)' : 'Password'}
						</label>
						<input
							id="user-password"
							type="password"
							bind:value={userFormData.password}
							required={!editingUser && userFormData.requires_password}
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
						/>
					</div>
				{/if}

				{#if editingUser}
					<div>
						<label class="flex items-center gap-2">
							<input
								type="checkbox"
								bind:checked={userFormData.is_active}
								class="h-4 w-4 rounded border-slate-300 text-primary-600"
							/>
							<span class="text-sm text-slate-700">Active</span>
						</label>
					</div>
				{/if}
			</form>

			<div class="mt-6 flex justify-end gap-3">
				<Button variant="secondary" on:click={() => showUserModal = false}>
					Cancel
				</Button>
				<Button loading={savingUser} on:click={handleSaveUser}>
					{editingUser ? 'Save Changes' : 'Create User'}
				</Button>
			</div>
		</div>
	</div>
{/if}
