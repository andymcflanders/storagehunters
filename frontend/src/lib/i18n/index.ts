import { browser } from '$app/environment';
import { register, init, getLocaleFromNavigator, locale } from 'svelte-i18n';

// Register locales
register('en', () => import('./locales/en.json'));
register('no', () => import('./locales/no.json'));

// Initialize i18n
export function setupI18n(initialLocale?: string) {
	init({
		fallbackLocale: 'en',
		initialLocale: initialLocale || (browser ? getLocaleFromNavigator()?.split('-')[0] : 'en')
	});
}

// Set locale (called when user changes language)
export function setLocale(newLocale: string) {
	locale.set(newLocale);
	if (browser) {
		localStorage.setItem('storagehub_locale', newLocale);
	}
}

// Get stored locale from localStorage
export function getStoredLocale(): string | null {
	if (browser) {
		return localStorage.getItem('storagehub_locale');
	}
	return null;
}

// Export commonly used functions from svelte-i18n
export { _, t, locale, locales } from 'svelte-i18n';
