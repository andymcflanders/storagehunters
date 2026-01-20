<script lang="ts">
	import { _ } from '$lib/i18n';
	import { createEventDispatcher } from 'svelte';
	import type { DocSection } from '$lib/docs';

	export let userGuideSections: DocSection[] = [];
	export let technicalSections: DocSection[] = [];
	export let activeSection: string = '';
	export let activeCategory: 'userGuide' | 'technical' = 'userGuide';
	export let isMobileOpen: boolean = false;

	const dispatch = createEventDispatcher<{
		selectSection: { sectionId: string; category: 'userGuide' | 'technical' };
		close: void;
	}>();

	function selectSection(sectionId: string, category: 'userGuide' | 'technical') {
		dispatch('selectSection', { sectionId, category });
		if (isMobileOpen) {
			dispatch('close');
		}
	}

	$: currentSections = activeCategory === 'userGuide' ? userGuideSections : technicalSections;
</script>

<!-- Mobile overlay -->
{#if isMobileOpen}
	<div
		class="fixed inset-0 z-40 bg-black/50 lg:hidden"
		on:click={() => dispatch('close')}
		on:keydown={(e) => e.key === 'Escape' && dispatch('close')}
		role="button"
		tabindex="0"
		aria-label="Close sidebar"
	/>
{/if}

<!-- Sidebar -->
<aside
	class="fixed left-0 top-0 z-50 h-full w-72 transform overflow-y-auto border-r border-slate-200 bg-white transition-transform duration-300 dark:border-slate-700 dark:bg-slate-900 lg:relative lg:z-0 lg:translate-x-0"
	class:translate-x-0={isMobileOpen}
	class:-translate-x-full={!isMobileOpen}
>
	<div class="sticky top-0 border-b border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
		<!-- Mobile close button -->
		<div class="mb-4 flex items-center justify-between lg:hidden">
			<h2 class="text-lg font-semibold text-slate-900 dark:text-white">{$_('docs.title')}</h2>
			<button
				class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
				on:click={() => dispatch('close')}
			>
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Category tabs -->
		<div class="flex gap-2">
			<button
				class="flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors {activeCategory === 'userGuide'
					? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
					: 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'}"
				on:click={() => {
					activeCategory = 'userGuide';
					if (userGuideSections.length > 0) {
						selectSection(userGuideSections[0].id, 'userGuide');
					}
				}}
			>
				{$_('docs.categories.userGuide')}
			</button>
			<button
				class="flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors {activeCategory === 'technical'
					? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
					: 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'}"
				on:click={() => {
					activeCategory = 'technical';
					if (technicalSections.length > 0) {
						selectSection(technicalSections[0].id, 'technical');
					}
				}}
			>
				{$_('docs.categories.technical')}
			</button>
		</div>
	</div>

	<!-- Section list -->
	<nav class="p-4">
		<ul class="space-y-1">
			{#each currentSections as section}
				<li>
					<button
						class="w-full rounded-lg px-3 py-2 text-left text-sm transition-colors {activeSection === section.id
							? 'bg-primary-50 font-medium text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
							: 'text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'}"
						on:click={() => selectSection(section.id, activeCategory)}
					>
						{$_(section.titleKey)}
					</button>
				</li>
			{/each}
		</ul>
	</nav>
</aside>
