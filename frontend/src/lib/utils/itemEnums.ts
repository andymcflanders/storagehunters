/**
 * Translation key maps for item enums (condition, seasonal).
 *
 * Backend stores these as snake_case enum values; locale files use
 * camelCase keys. This bridges the two so components can write
 * `$_(CONDITION_KEYS[item.condition])` instead of hardcoding labels.
 */

import type { Condition, Seasonal } from '$lib/types';

export const CONDITION_KEYS: Record<Condition, string> = {
	good: 'items.conditions.good',
	fair: 'items.conditions.fair',
	damaged: 'items.conditions.damaged',
	needs_repair: 'items.conditions.needsRepair'
};

export const SEASONAL_KEYS: Record<Seasonal, string> = {
	none: 'items.seasonal.none',
	spring: 'items.seasonal.spring',
	summer: 'items.seasonal.summer',
	fall: 'items.seasonal.fall',
	winter: 'items.seasonal.winter',
	holiday: 'items.seasonal.holiday'
};
