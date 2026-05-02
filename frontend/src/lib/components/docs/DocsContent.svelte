<script lang="ts">
	import { onMount } from 'svelte';
	import { _, locale } from '$lib/i18n';
	import { marked } from 'marked';
	import type { DocSection } from '$lib/docs';

	export let section: DocSection | null = null;
	export let allSections: DocSection[] = [];
	export let onNavigate: (sectionId: string) => void = () => {};

	let renderedContent = '';

	// Configure marked options
	marked.setOptions({
		gfm: true,
		breaks: true
	});

	// Pick the markdown body for the user's locale, falling back to English.
	// Re-runs when either the section or the user's language changes so a
	// language switch refreshes the content immediately.
	$: if (section?.content) {
		const lang = $locale || 'en';
		const body = section.content[lang] ?? section.content.en ?? Object.values(section.content)[0] ?? '';
		renderedContent = marked.parse(body) as string;
	}

	$: currentIndex = allSections.findIndex((s) => s.id === section?.id);
	$: prevSection = currentIndex > 0 ? allSections[currentIndex - 1] : null;
	$: nextSection = currentIndex < allSections.length - 1 ? allSections[currentIndex + 1] : null;

	function scrollToTop() {
		const contentEl = document.getElementById('docs-content');
		if (contentEl) {
			contentEl.scrollTop = 0;
		}
	}

	$: if (section) {
		scrollToTop();
	}
</script>

<div id="docs-content" class="flex-1 overflow-y-auto">
	{#if section}
		<article class="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
			<!-- Rendered markdown content -->
			<div class="prose prose-slate dark:prose-invert max-w-none">
				{@html renderedContent}
			</div>

			<!-- Navigation buttons -->
			{#if prevSection || nextSection}
				<div class="mt-12 flex items-center justify-between border-t border-slate-200 pt-6 dark:border-slate-700">
					{#if prevSection}
						<button
							class="group flex items-center gap-2 text-sm text-slate-600 transition-colors hover:text-primary-600 dark:text-slate-400 dark:hover:text-primary-400"
							on:click={() => onNavigate(prevSection.id)}
						>
							<svg
								class="h-5 w-5 transition-transform group-hover:-translate-x-1"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
							</svg>
							<span class="flex flex-col items-start">
								<span class="text-xs text-slate-400 dark:text-slate-500">{$_('docs.navigation.previous')}</span>
								<span class="font-medium">{$_(prevSection.titleKey)}</span>
							</span>
						</button>
					{:else}
						<div />
					{/if}

					{#if nextSection}
						<button
							class="group flex items-center gap-2 text-right text-sm text-slate-600 transition-colors hover:text-primary-600 dark:text-slate-400 dark:hover:text-primary-400"
							on:click={() => onNavigate(nextSection.id)}
						>
							<span class="flex flex-col items-end">
								<span class="text-xs text-slate-400 dark:text-slate-500">{$_('docs.navigation.next')}</span>
								<span class="font-medium">{$_(nextSection.titleKey)}</span>
							</span>
							<svg
								class="h-5 w-5 transition-transform group-hover:translate-x-1"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</button>
					{:else}
						<div />
					{/if}
				</div>
			{/if}
		</article>
	{:else}
		<div class="flex h-full items-center justify-center">
			<p class="text-slate-500 dark:text-slate-400">{$_('common.loading')}</p>
		</div>
	{/if}
</div>
