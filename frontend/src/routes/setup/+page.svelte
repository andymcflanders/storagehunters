<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { _, locale } from '$lib/i18n';
	import { auth } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { Button, Card, Input } from '$lib/components';

	type Step = 'welcome' | 'admin' | 'ai' | 'location' | 'done';
	const STEPS: Step[] = ['welcome', 'admin', 'ai', 'location', 'done'];

	let step: Step = 'welcome';
	let submitting = false;

	// Step 2 — admin
	let adminName = '';
	let adminEmail = '';
	let adminPassword = '';
	let adminLanguage: 'en' | 'no' = 'en';

	// Step 3 — AI
	let openaiApiKey = '';
	let supportedLanguagesInput = 'en, no';

	// Step 4 — first location
	let locationName = '';
	let locationDescription = '';
	let locationAddress = '';

	// Default the admin's UI language to whatever the browser is currently
	// using, so the wizard's later steps stay in the same language as the
	// user just saw on the welcome screen.
	$: if ($locale === 'no' || $locale === 'en') {
		adminLanguage = $locale;
	}

	// Guard: if setup is already complete, don't even let users see this
	// page. Don't trust the layout-level redirect alone — somebody might
	// hit /setup directly to try and create a second admin.
	onMount(async () => {
		try {
			const r = await fetch('/api/setup/status', { credentials: 'include' });
			if (r.ok) {
				const data = await r.json();
				if (!data.needs_setup) goto('/');
			}
		} catch {
			// If the probe fails we let the user proceed and surface any
			// error from /complete — better than blocking on a hiccup.
		}
	});

	$: stepIndex = STEPS.indexOf(step);

	function next() {
		const i = STEPS.indexOf(step);
		if (i < STEPS.length - 1) step = STEPS[i + 1];
	}

	function back() {
		const i = STEPS.indexOf(step);
		if (i > 0) step = STEPS[i - 1];
	}

	function handleAdminContinue() {
		if (!adminName.trim()) return;
		next();
	}

	async function handleFinish() {
		submitting = true;
		try {
			const supported = supportedLanguagesInput
				.split(',')
				.map((s) => s.trim().toLowerCase())
				.filter(Boolean);

			const payload: Record<string, unknown> = {
				admin_name: adminName.trim(),
				admin_email: adminEmail.trim() || null,
				admin_password: adminPassword || null,
				admin_language: adminLanguage,
				openai_api_key: openaiApiKey.trim() || null,
				supported_languages: supported.length ? supported : null,
				default_language: supported[0] || null
			};

			if (locationName.trim()) {
				payload.first_location = {
					name: locationName.trim(),
					description: locationDescription.trim() || null,
					address: locationAddress.trim() || null
				};
			}

			const response = await fetch('/api/setup/complete', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify(payload)
			});

			if (!response.ok) {
				const err = await response.json().catch(() => ({ detail: 'Setup failed' }));
				throw new Error(err.detail || 'Setup failed');
			}

			// Pull the new session cookie's user into the store so the
			// dashboard greets us by name instead of bouncing to /login.
			await auth.initialize();
			step = 'done';
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Setup failed';
			toast.error(message);
		} finally {
			submitting = false;
		}
	}

	function openApp() {
		goto('/');
	}
</script>

<svelte:head>
	<title>Setup - {$_('app.name')}</title>
</svelte:head>

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
	<div class="mx-auto max-w-xl px-4 py-12 sm:px-6">
		<!-- Logo -->
		<div class="mb-8 flex items-center justify-center gap-2">
			<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600 text-white">
				<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
				</svg>
			</div>
			<span class="text-2xl font-bold text-slate-900 dark:text-white">{$_('app.name')}</span>
		</div>

		<!-- Progress -->
		<div class="mb-6 flex gap-1.5">
			{#each STEPS as _s, i}
				<div
					class="h-1 flex-1 rounded-full transition-colors {i <= stepIndex
						? 'bg-primary-600'
						: 'bg-slate-200 dark:bg-slate-700'}"
				></div>
			{/each}
		</div>

		<Card>
			{#if step === 'welcome'}
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{$_('setup.welcome.title')}</h1>
				<p class="mt-3 text-slate-600 dark:text-slate-300">{$_('setup.welcome.intro')}</p>
				<div class="mt-6">
					<Button on:click={next}>{$_('setup.welcome.start')}</Button>
				</div>
			{:else if step === 'admin'}
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{$_('setup.admin.title')}</h1>
				<p class="mt-2 text-slate-600 dark:text-slate-300">{$_('setup.admin.intro')}</p>

				<form on:submit|preventDefault={handleAdminContinue} class="mt-6 space-y-4">
					<Input
						label={$_('setup.admin.name')}
						placeholder={$_('setup.admin.namePlaceholder')}
						bind:value={adminName}
						required
						id="admin-name"
					/>
					<Input
						label={$_('setup.admin.email')}
						placeholder={$_('setup.admin.emailPlaceholder')}
						bind:value={adminEmail}
						type="email"
						id="admin-email"
					/>
					<Input
						label={$_('setup.admin.password')}
						bind:value={adminPassword}
						type="password"
						id="admin-password"
					/>
					<p class="text-xs text-slate-500 dark:text-slate-400">{$_('setup.admin.passwordHelp')}</p>

					<div>
						<label for="admin-language" class="label">{$_('setup.admin.language')}</label>
						<select id="admin-language" class="input" bind:value={adminLanguage}>
							<option value="en">English</option>
							<option value="no">Norsk</option>
						</select>
					</div>
				</form>

				<div class="mt-6 flex justify-between">
					<Button variant="ghost" on:click={back}>{$_('setup.buttons.back')}</Button>
					<Button on:click={handleAdminContinue} disabled={!adminName.trim()}>
						{$_('setup.buttons.continue')}
					</Button>
				</div>
			{:else if step === 'ai'}
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{$_('setup.ai.title')}</h1>
				<p class="mt-2 text-slate-600 dark:text-slate-300">{$_('setup.ai.intro')}</p>

				<div class="mt-6 space-y-4">
					<div>
						<Input
							label={$_('setup.ai.keyLabel')}
							placeholder={$_('setup.ai.keyPlaceholder')}
							bind:value={openaiApiKey}
							type="password"
							id="setup-openai-key"
						/>
						<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{$_('setup.ai.keyHelp')}</p>
					</div>

					<div>
						<Input
							label={$_('setup.ai.languagesLabel')}
							bind:value={supportedLanguagesInput}
							id="setup-languages"
						/>
						<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{$_('setup.ai.languagesHelp')}</p>
					</div>
				</div>

				<div class="mt-6 flex justify-between">
					<Button variant="ghost" on:click={back}>{$_('setup.buttons.back')}</Button>
					<div class="flex gap-2">
						<Button variant="secondary" on:click={next}>{$_('setup.buttons.skip')}</Button>
						<Button on:click={next}>{$_('setup.buttons.continue')}</Button>
					</div>
				</div>
			{:else if step === 'location'}
				<h1 class="text-2xl font-bold text-slate-900 dark:text-white">{$_('setup.location.title')}</h1>
				<p class="mt-2 text-slate-600 dark:text-slate-300">{$_('setup.location.intro')}</p>

				<div class="mt-6 space-y-4">
					<Input
						label={$_('common.name')}
						placeholder={$_('setup.location.namePlaceholder')}
						bind:value={locationName}
						id="setup-location-name"
					/>
					<Input
						label={$_('common.description')}
						bind:value={locationDescription}
						id="setup-location-description"
					/>
					<Input
						label={$_('locations.address')}
						bind:value={locationAddress}
						id="setup-location-address"
					/>
				</div>

				<div class="mt-6 flex justify-between">
					<Button variant="ghost" on:click={back}>{$_('setup.buttons.back')}</Button>
					<Button loading={submitting} on:click={handleFinish}>
						{$_('setup.buttons.finish')}
					</Button>
				</div>
			{:else if step === 'done'}
				<div class="text-center">
					<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
						<svg class="h-8 w-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<h1 class="mt-4 text-2xl font-bold text-slate-900 dark:text-white">{$_('setup.done.title')}</h1>
					<p class="mt-2 text-slate-600 dark:text-slate-300">{$_('setup.done.intro')}</p>
					<Button class="mt-6" on:click={openApp}>{$_('setup.done.finish')}</Button>
				</div>
			{/if}
		</Card>
	</div>
</div>
