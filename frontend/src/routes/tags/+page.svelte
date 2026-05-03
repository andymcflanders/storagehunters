<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { tags } from '$lib/api';
	import { Card, Button, Input, Modal } from '$lib/components';
	import type { TagResponse } from '$lib/api/tags';

	let tagList: TagResponse[] = [];
	let loading = true;
	let showCreateModal = false;
	let showMergeModal = false;
	let creating = false;
	let merging = false;

	let newTagName = '';
	let selectedTags: Set<string> = new Set();
	let mergeTargetId = '';

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		await loadTags();
	});

	async function loadTags() {
		loading = true;
		try {
			tagList = await tags.listTags();
		} catch (error) {
			toast.error('Failed to load tags');
		} finally {
			loading = false;
		}
	}

	async function handleCreate() {
		if (!newTagName.trim()) return;

		creating = true;
		try {
			await tags.createTag(newTagName.trim());
			toast.success('Tag created');
			showCreateModal = false;
			newTagName = '';
			await loadTags();
		} catch (error) {
			toast.error('Failed to create tag');
		} finally {
			creating = false;
		}
	}

	async function handleDelete(tagId: string, tagName: string) {
		if (!confirm(`Delete tag "${tagName}"? This will remove it from all items.`)) return;

		try {
			await tags.deleteTag(tagId);
			toast.success('Tag deleted');
			await loadTags();
		} catch (error) {
			toast.error('Failed to delete tag');
		}
	}

	function toggleTagSelection(tagId: string) {
		if (selectedTags.has(tagId)) {
			selectedTags.delete(tagId);
		} else {
			selectedTags.add(tagId);
		}
		selectedTags = selectedTags; // Trigger reactivity
	}

	function openMergeModal() {
		if (selectedTags.size < 2) {
			toast.warning('Select at least 2 tags to merge');
			return;
		}
		mergeTargetId = Array.from(selectedTags)[0];
		showMergeModal = true;
	}

	async function handleMerge() {
		if (!mergeTargetId) return;

		const sourceIds = Array.from(selectedTags).filter(id => id !== mergeTargetId);
		if (sourceIds.length === 0) {
			toast.warning('Select tags to merge into the target');
			return;
		}

		merging = true;
		try {
			await tags.mergeTags(sourceIds, mergeTargetId);
			toast.success('Tags merged');
			showMergeModal = false;
			selectedTags = new Set();
			await loadTags();
		} catch (error) {
			toast.error('Failed to merge tags');
		} finally {
			merging = false;
		}
	}

	$: aiTags = tagList.filter(t => !t.user_created);
	$: userTags = tagList.filter(t => t.user_created);
</script>

<svelte:head>
	<title>Tags - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Tags</h1>
			<p class="mt-1 text-slate-500 dark:text-slate-400">Manage tags for organizing your items</p>
		</div>
		<div class="flex gap-2">
			{#if selectedTags.size >= 2}
				<Button variant="secondary" on:click={openMergeModal}>
					Merge Selected ({selectedTags.size})
				</Button>
			{/if}
			<Button on:click={() => (showCreateModal = true)}>
				<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
				</svg>
				Add Tag
			</Button>
		</div>
	</div>

	{#if loading}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each [1, 2, 3, 4, 5, 6] as _}
				<div class="h-20 animate-pulse rounded-xl bg-slate-200"></div>
			{/each}
		</div>
	{:else if tagList.length === 0}
		<Card>
			<div class="py-12 text-center">
				<svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
				</svg>
				<h3 class="mt-4 text-lg font-medium text-slate-900 dark:text-white">No tags yet</h3>
				<p class="mt-2 text-slate-500 dark:text-slate-400">Tags will appear here as you add items with AI classification or create them manually.</p>
			</div>
		</Card>
	{:else}
		<!-- User-created Tags -->
		{#if userTags.length > 0}
			<div>
				<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Manual Tags</h2>
				<div class="flex flex-wrap gap-2">
					{#each userTags as tag}
						<button
							class="group inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all
								{selectedTags.has(tag.id)
									? 'bg-primary-600 text-white'
									: 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200'}"
							on:click={() => toggleTagSelection(tag.id)}
						>
							{tag.name}
							<button
								class="rounded-full p-0.5 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-white/20"
								on:click|stopPropagation={() => handleDelete(tag.id, tag.name)}
							>
								<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</button>
					{/each}
				</div>
			</div>
		{/if}

		<!-- AI-generated Tags -->
		{#if aiTags.length > 0}
			<div>
				<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
					AI-Generated Tags
					<span class="ml-2 text-sm font-normal text-slate-500 dark:text-slate-400">({aiTags.length})</span>
				</h2>
				<div class="flex flex-wrap gap-2">
					{#each aiTags as tag}
						<button
							class="group inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all
								{selectedTags.has(tag.id)
									? 'bg-primary-600 text-white'
									: 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 hover:bg-blue-100'}"
							on:click={() => toggleTagSelection(tag.id)}
						>
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
							</svg>
							{tag.name}
							<button
								class="rounded-full p-0.5 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-white/20"
								on:click|stopPropagation={() => handleDelete(tag.id, tag.name)}
							>
								<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</button>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>

<!-- Create Modal -->
<Modal open={showCreateModal} title="Create Tag" on:close={() => (showCreateModal = false)}>
	<form on:submit|preventDefault={handleCreate}>
		<Input
			label="Tag Name"
			placeholder="e.g., electronics, winter-clothes"
			bind:value={newTagName}
			required
			id="tag-name"
		/>
	</form>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showCreateModal = false)}>Cancel</Button>
		<Button loading={creating} on:click={handleCreate}>Create Tag</Button>
	</svelte:fragment>
</Modal>

<!-- Merge Modal -->
<Modal open={showMergeModal} title="Merge Tags" on:close={() => (showMergeModal = false)}>
	<p class="mb-4 text-slate-600 dark:text-slate-400">
		Select the target tag. All other selected tags will be merged into it.
	</p>

	<div class="space-y-2">
		{#each Array.from(selectedTags) as tagId}
			{@const tag = tagList.find(t => t.id === tagId)}
			{#if tag}
				<label class="flex items-center gap-3 rounded-lg border p-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50
					{mergeTargetId === tagId ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-slate-200 dark:border-slate-700'}">
					<input
						type="radio"
						name="merge-target"
						value={tagId}
						bind:group={mergeTargetId}
						class="h-4 w-4 text-primary-600 dark:text-primary-400"
					/>
					<span class="font-medium">{tag.name}</span>
					{#if mergeTargetId === tagId}
						<span class="ml-auto text-xs text-primary-600 dark:text-primary-400">Target</span>
					{/if}
				</label>
			{/if}
		{/each}
	</div>

	<svelte:fragment slot="footer">
		<Button variant="secondary" on:click={() => (showMergeModal = false)}>Cancel</Button>
		<Button loading={merging} on:click={handleMerge}>Merge Tags</Button>
	</svelte:fragment>
</Modal>
