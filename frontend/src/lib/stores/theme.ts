/**
 * Theme store for dark mode.
 */

import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'system';

function getInitialTheme(): Theme {
	if (!browser) return 'system';

	const stored = localStorage.getItem('storagehub_theme');
	if (stored === 'light' || stored === 'dark' || stored === 'system') {
		return stored;
	}
	return 'system';
}

function createThemeStore() {
	const { subscribe, set, update } = writable<Theme>(getInitialTheme());

	function applyTheme(theme: Theme) {
		if (!browser) return;

		const isDark =
			theme === 'dark' ||
			(theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

		document.documentElement.classList.toggle('dark', isDark);
		localStorage.setItem('storagehub_theme', theme);
	}

	// Apply initial theme
	if (browser) {
		applyTheme(getInitialTheme());

		// Listen for system theme changes
		window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
			const current = localStorage.getItem('storagehub_theme') as Theme;
			if (current === 'system') {
				applyTheme('system');
			}
		});
	}

	return {
		subscribe,
		set: (value: Theme) => {
			set(value);
			applyTheme(value);
		},
		toggle: () => {
			update((current) => {
				const next = current === 'light' ? 'dark' : current === 'dark' ? 'system' : 'light';
				applyTheme(next);
				return next;
			});
		}
	};
}

export const theme = createThemeStore();
