<script lang="ts">
	import { onMount } from 'svelte';
	import { reminders } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import type { Reminder, ReminderType } from '$lib/api/reminders';

	let loading = true;
	let reminderList: Reminder[] = [];
	let overdueCount = 0;
	let upcomingCount = 0;
	let showCompleted = false;
	let showCreateModal = false;

	// Create form
	let newTitle = '';
	let newDescription = '';
	let newType: ReminderType = 'custom';
	let newDueDate = '';
	let newIsRecurring = false;
	let newRecurrenceDays: number | null = null;
	let creating = false;

	const reminderTypes: { value: ReminderType; label: string }[] = [
		{ value: 'custom', label: 'Custom' },
		{ value: 'check_item', label: 'Check Item' },
		{ value: 'expiration', label: 'Expiration' },
		{ value: 'maintenance', label: 'Maintenance' },
		{ value: 'restock', label: 'Restock' }
	];

	onMount(async () => {
		await loadReminders();
	});

	async function loadReminders() {
		loading = true;
		try {
			const response = await reminders.listReminders({ include_completed: showCompleted });
			reminderList = response.items;
			overdueCount = response.overdue_count;
			upcomingCount = response.upcoming_count;
		} catch {
			toast.error('Failed to load reminders');
		} finally {
			loading = false;
		}
	}

	async function handleComplete(reminder: Reminder) {
		try {
			await reminders.completeReminder(reminder.id);
			toast.success(reminder.is_recurring ? 'Reminder completed, next one created' : 'Reminder completed');
			await loadReminders();
		} catch {
			toast.error('Failed to complete reminder');
		}
	}

	async function handleDelete(reminder: Reminder) {
		if (!confirm(`Delete "${reminder.title}"?`)) return;
		try {
			await reminders.deleteReminder(reminder.id);
			toast.success('Reminder deleted');
			await loadReminders();
		} catch {
			toast.error('Failed to delete reminder');
		}
	}

	async function handleCreate() {
		if (!newTitle.trim() || !newDueDate) {
			toast.error('Please fill in required fields');
			return;
		}

		creating = true;
		try {
			await reminders.createReminder({
				title: newTitle.trim(),
				description: newDescription.trim() || null,
				reminder_type: newType,
				due_date: new Date(newDueDate).toISOString(),
				is_recurring: newIsRecurring,
				recurrence_days: newIsRecurring ? newRecurrenceDays : null
			});
			toast.success('Reminder created');
			showCreateModal = false;
			resetForm();
			await loadReminders();
		} catch {
			toast.error('Failed to create reminder');
		} finally {
			creating = false;
		}
	}

	function resetForm() {
		newTitle = '';
		newDescription = '';
		newType = 'custom';
		newDueDate = '';
		newIsRecurring = false;
		newRecurrenceDays = null;
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = date.getTime() - now.getTime();
		const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

		if (days < 0) return `${Math.abs(days)} days overdue`;
		if (days === 0) return 'Due today';
		if (days === 1) return 'Due tomorrow';
		if (days < 7) return `Due in ${days} days`;
		return date.toLocaleDateString();
	}

	function getTypeIcon(type: ReminderType): string {
		switch (type) {
			case 'check_item':
				return 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4';
			case 'expiration':
				return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z';
			case 'maintenance':
				return 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z';
			case 'restock':
				return 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z';
			default:
				return 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9';
		}
	}

	$: {
		showCompleted;
		loadReminders();
	}
</script>

<svelte:head>
	<title>Reminders - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Reminders</h1>
			<p class="mt-1 text-slate-500 dark:text-slate-400">
				{#if overdueCount > 0}
					<span class="text-red-500">{overdueCount} overdue</span> ·
				{/if}
				{upcomingCount} upcoming
			</p>
		</div>
		<div class="flex items-center gap-3">
			<label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
				<input
					type="checkbox"
					bind:checked={showCompleted}
					class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400 focus:ring-primary-500"
				/>
				Show completed
			</label>
			<button
				on:click={() => (showCreateModal = true)}
				class="btn-primary"
			>
				<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
				</svg>
				New Reminder
			</button>
		</div>
	</div>

	<!-- Reminders List -->
	{#if loading}
		<div class="flex justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
		</div>
	{:else if reminderList.length === 0}
		<div class="rounded-xl bg-white p-12 text-center shadow-sm dark:bg-slate-800">
			<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-700">
				<svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
				</svg>
			</div>
			<h2 class="mt-4 text-lg font-semibold text-slate-900 dark:text-white">No reminders</h2>
			<p class="mt-2 text-slate-500 dark:text-slate-400">Create a reminder to stay organized.</p>
			<button
				on:click={() => (showCreateModal = true)}
				class="btn-primary mt-6"
			>
				Create Reminder
			</button>
		</div>
	{:else}
		<div class="space-y-3">
			{#each reminderList as reminder}
				<div class="rounded-xl bg-white p-4 shadow-sm dark:bg-slate-800 {reminder.is_overdue ? 'border-l-4 border-red-500' : ''} {reminder.is_completed ? 'opacity-60' : ''}">
					<div class="flex items-start gap-4">
						<div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg {reminder.is_overdue ? 'bg-red-100 text-red-600 dark:bg-red-900/30' : 'bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400'}">
							<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getTypeIcon(reminder.reminder_type)} />
							</svg>
						</div>

						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2">
								<h3 class="font-medium text-slate-900 dark:text-white {reminder.is_completed ? 'line-through' : ''}">{reminder.title}</h3>
								{#if reminder.is_recurring}
									<span class="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
										Recurring
									</span>
								{/if}
							</div>

							{#if reminder.description}
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{reminder.description}</p>
							{/if}

							<div class="mt-2 flex flex-wrap items-center gap-3 text-sm">
								<span class="{reminder.is_overdue ? 'text-red-500' : 'text-slate-500 dark:text-slate-400'}">
									{formatDate(reminder.due_date)}
								</span>

								{#if reminder.item_name}
									<span class="flex items-center gap-1 text-slate-500 dark:text-slate-400">
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
										</svg>
										{reminder.item_name}
									</span>
								{/if}

								{#if reminder.container_name}
									<span class="flex items-center gap-1 text-slate-500 dark:text-slate-400">
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
										</svg>
										{reminder.container_name}
									</span>
								{/if}
							</div>
						</div>

						<div class="flex items-center gap-2">
							{#if !reminder.is_completed}
								<button
									on:click={() => handleComplete(reminder)}
									class="rounded-lg p-2 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
									title="Mark complete"
								>
									<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
									</svg>
								</button>
							{/if}
							<button
								on:click={() => handleDelete(reminder)}
								class="rounded-lg p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
								title="Delete"
							>
								<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Create Modal -->
{#if showCreateModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-800">
			<h2 class="text-xl font-bold text-slate-900 dark:text-white">New Reminder</h2>

			<form on:submit|preventDefault={handleCreate} class="mt-6 space-y-4">
				<div>
					<label class="label" for="title">Title *</label>
					<input
						type="text"
						id="title"
						bind:value={newTitle}
						class="input"
						placeholder="Reminder title"
						required
					/>
				</div>

				<div>
					<label class="label" for="description">Description</label>
					<textarea
						id="description"
						bind:value={newDescription}
						class="input"
						rows="2"
						placeholder="Optional description"
					></textarea>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="label" for="type">Type</label>
						<select id="type" bind:value={newType} class="input">
							{#each reminderTypes as type}
								<option value={type.value}>{type.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<label class="label" for="due_date">Due Date *</label>
						<input
							type="datetime-local"
							id="due_date"
							bind:value={newDueDate}
							class="input"
							required
						/>
					</div>
				</div>

				<div class="space-y-3">
					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							bind:checked={newIsRecurring}
							class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400 focus:ring-primary-500"
						/>
						<span class="text-sm text-slate-700 dark:text-slate-300">Recurring reminder</span>
					</label>

					{#if newIsRecurring}
						<div>
							<label class="label" for="recurrence">Repeat every (days)</label>
							<input
								type="number"
								id="recurrence"
								bind:value={newRecurrenceDays}
								class="input"
								min="1"
								placeholder="e.g., 7 for weekly"
							/>
						</div>
					{/if}
				</div>

				<div class="flex justify-end gap-3 pt-4">
					<button
						type="button"
						on:click={() => { showCreateModal = false; resetForm(); }}
						class="btn-secondary"
					>
						Cancel
					</button>
					<button type="submit" class="btn-primary" disabled={creating}>
						{creating ? 'Creating...' : 'Create Reminder'}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
