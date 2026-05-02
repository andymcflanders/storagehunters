/**
 * Utilities for picking a string from an AI-generated translations dict.
 *
 * AI-generated content is stored on items as a `Record<string, string>`
 * keyed by ISO language code (e.g. {"en": "Red sweater", "no": "Rød genser"}).
 * The set of keys depends on what AISettings.supported_languages was at the
 * time the item was classified — it isn't guaranteed to match the user's
 * current locale.
 */

import { get } from 'svelte/store';
import { locale } from '$lib/i18n';

const DEFAULT_FALLBACK = 'en';

/**
 * Resolve a translations dict to a single string for the user's locale.
 *
 * Lookup order:
 *   1. Exact match on the user's locale.
 *   2. Default fallback (English).
 *   3. Any non-empty value present in the dict.
 *   4. Empty string.
 */
export function getLocalizedAI(
	translations: Record<string, string> | null | undefined,
	preferredLocale?: string
): string {
	if (!translations) return '';
	const lang = preferredLocale || get(locale) || DEFAULT_FALLBACK;
	if (translations[lang]) return translations[lang];
	if (translations[DEFAULT_FALLBACK]) return translations[DEFAULT_FALLBACK];
	for (const value of Object.values(translations)) {
		if (value) return value;
	}
	return '';
}

/**
 * Returns the list of [code, value] pairs for a translations dict, sorted
 * with the user's locale first, then the default fallback, then the rest.
 * Useful for components that want to show all translations (e.g. the
 * detail page's language toggle).
 */
export function getAllTranslations(
	translations: Record<string, string> | null | undefined,
	preferredLocale?: string
): Array<[string, string]> {
	if (!translations) return [];
	const lang = preferredLocale || get(locale) || DEFAULT_FALLBACK;
	const ordered = new Set<string>();
	if (translations[lang]) ordered.add(lang);
	if (translations[DEFAULT_FALLBACK]) ordered.add(DEFAULT_FALLBACK);
	for (const code of Object.keys(translations)) ordered.add(code);
	return Array.from(ordered)
		.filter((code) => translations[code])
		.map((code) => [code, translations[code]] as [string, string]);
}
