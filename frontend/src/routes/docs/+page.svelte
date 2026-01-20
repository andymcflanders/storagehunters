<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { _ } from '$lib/i18n';
	import { user } from '$lib/stores/auth';
	import { DocsSidebar, DocsContent } from '$lib/components/docs';
	import { userGuideSections, technicalSections, type DocSection } from '$lib/docs';

	let activeCategory: 'userGuide' | 'technical' = 'userGuide';
	let activeSection: string = userGuideSections[0]?.id || '';
	let currentSection: DocSection | null = null;
	let isMobileSidebarOpen = false;

	// Redirect to login if not authenticated
	$: if (!$user) {
		goto('/login');
	}

	// Update current section when active section changes
	$: {
		const sections = activeCategory === 'userGuide' ? userGuideSections : technicalSections;
		currentSection = sections.find((s) => s.id === activeSection) || sections[0] || null;
	}

	$: allCurrentSections = activeCategory === 'userGuide' ? userGuideSections : technicalSections;

	function handleSelectSection(event: CustomEvent<{ sectionId: string; category: 'userGuide' | 'technical' }>) {
		const { sectionId, category } = event.detail;
		activeCategory = category;
		activeSection = sectionId;
	}

	function handleNavigate(sectionId: string) {
		activeSection = sectionId;
	}

	onMount(() => {
		// Check URL hash for initial section
		const hash = window.location.hash.slice(1);
		if (hash) {
			// Try to find section in user guide
			let found = userGuideSections.find((s) => s.id === hash);
			if (found) {
				activeCategory = 'userGuide';
				activeSection = hash;
			} else {
				// Try technical sections
				found = technicalSections.find((s) => s.id === hash);
				if (found) {
					activeCategory = 'technical';
					activeSection = hash;
				}
			}
		}
	});

	// Update URL hash when section changes
	$: if (typeof window !== 'undefined' && activeSection) {
		window.history.replaceState(null, '', `#${activeSection}`);
	}
</script>

<svelte:head>
	<title>{$_('docs.title')} - {$_('app.name')}</title>
</svelte:head>

{#if $user}
	<div class="flex h-[calc(100vh-8rem)] -mx-4 sm:-mx-6 lg:-mx-8 -my-8">
		<!-- Sidebar -->
		<DocsSidebar
			{userGuideSections}
			{technicalSections}
			{activeSection}
			bind:activeCategory
			isMobileOpen={isMobileSidebarOpen}
			on:selectSection={handleSelectSection}
			on:close={() => (isMobileSidebarOpen = false)}
		/>

		<!-- Main content area -->
		<div class="flex flex-1 flex-col">
			<!-- Mobile header -->
			<div class="flex items-center gap-4 border-b border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900 lg:hidden">
				<button
					class="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
					on:click={() => (isMobileSidebarOpen = true)}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</button>
				<div>
					<h1 class="text-lg font-semibold text-slate-900 dark:text-white">{$_('docs.title')}</h1>
					{#if currentSection}
						<p class="text-sm text-slate-500 dark:text-slate-400">{$_(currentSection.titleKey)}</p>
					{/if}
				</div>
			</div>

			<!-- Content -->
			<DocsContent
				section={currentSection}
				allSections={allCurrentSections}
				onNavigate={handleNavigate}
			/>
		</div>
	</div>
{/if}
