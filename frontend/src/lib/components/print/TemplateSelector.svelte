<script lang="ts">
	import type { LabelTemplate } from '$lib/types';

	export let selected: LabelTemplate = 'qr_only';
	export let suggestedTemplate: LabelTemplate | null = null;

	interface TemplateOption {
		value: LabelTemplate;
		name: string;
		description: string;
		icon: string;
	}

	const templates: TemplateOption[] = [
		{
			value: 'qr_only',
			name: 'QR Only',
			description: 'Compact QR code with container name',
			icon: 'qr'
		},
		{
			value: 'qr_ai_summary',
			name: 'QR + Summary',
			description: 'QR code with AI-generated content summary',
			icon: 'summary'
		},
		{
			value: 'qr_full_contents',
			name: 'Full Contents',
			description: 'QR code with complete item list',
			icon: 'list'
		},
		{
			value: 'a4_full_details',
			name: 'A4 Full Details',
			description: 'Full page with item table and thumbnails',
			icon: 'document'
		}
	];
</script>

<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
	{#each templates as template}
		<button
			type="button"
			class="relative flex flex-col items-center p-4 border-2 rounded-lg transition-all {selected ===
			template.value
				? 'border-blue-500 bg-blue-50'
				: 'border-slate-200 hover:border-slate-300 bg-white'}"
			on:click={() => (selected = template.value)}
		>
			<!-- Suggested badge -->
			{#if suggestedTemplate === template.value}
				<span
					class="absolute -top-2 -right-2 px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full"
				>
					Suggested
				</span>
			{/if}

			<!-- Icon -->
			<div
				class="w-12 h-12 rounded-lg flex items-center justify-center mb-2 {selected ===
				template.value
					? 'bg-blue-100 text-blue-600'
					: 'bg-slate-100 text-slate-500'}"
			>
				{#if template.icon === 'qr'}
					<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h2M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
						/>
					</svg>
				{:else if template.icon === 'summary'}
					<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
				{:else if template.icon === 'list'}
					<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 6h16M4 10h16M4 14h16M4 18h16"
						/>
					</svg>
				{:else if template.icon === 'document'}
					<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 7h4m-4 4h4m-4 4h4"
						/>
					</svg>
				{/if}
			</div>

			<!-- Name -->
			<span
				class="text-sm font-medium {selected === template.value
					? 'text-blue-700'
					: 'text-slate-700'}"
			>
				{template.name}
			</span>

			<!-- Description -->
			<span class="text-xs text-slate-500 text-center mt-1">
				{template.description}
			</span>

			<!-- Selected indicator -->
			{#if selected === template.value}
				<div class="absolute top-2 left-2">
					<svg class="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
			{/if}
		</button>
	{/each}
</div>
