import { waitLocale } from 'svelte-i18n';
import { setupI18n } from '$lib/i18n';

// Run once per request on the server and once on hydration in the
// browser. setupI18n() registers the locales and triggers the async
// load; waitLocale() blocks the page render until that load resolves.
// Without this gate the very first render after a deploy can hit
// "Cannot format a message without first setting the initial locale"
// because $_('...') runs before svelte-i18n finishes loading the JSON.

export const load = async () => {
	setupI18n();
	await waitLocale();
	return {};
};
