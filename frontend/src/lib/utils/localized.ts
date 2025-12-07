/**
 * Utilities for getting localized AI content based on user's language preference.
 */

import { get } from 'svelte/store';
import { locale } from '$lib/i18n';

/**
 * Get localized content from AI-generated fields.
 * Falls back to English if Norwegian is not available, and vice versa.
 */
export function getLocalizedAI(
	englishValue: string | null | undefined,
	norwegianValue: string | null | undefined,
	preferredLocale?: string
): string {
	const currentLocale = preferredLocale || get(locale) || 'en';
	const isNorwegian = currentLocale === 'no';

	if (isNorwegian) {
		// Prefer Norwegian, fall back to English
		return norwegianValue || englishValue || '';
	} else {
		// Prefer English, fall back to Norwegian
		return englishValue || norwegianValue || '';
	}
}

/**
 * Get both language versions for display with toggle.
 */
export function getBothVersions(
	englishValue: string | null | undefined,
	norwegianValue: string | null | undefined
): { en: string; no: string; hasBoth: boolean } {
	return {
		en: englishValue || '',
		no: norwegianValue || '',
		hasBoth: !!(englishValue && norwegianValue)
	};
}
