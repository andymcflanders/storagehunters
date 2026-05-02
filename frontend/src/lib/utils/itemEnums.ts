/**
 * Translation key maps for item / container enums.
 *
 * Backend stores values as snake_case; locale files use camelCase keys.
 * Components reference `$_(CONDITION_KEYS[item.condition])` etc. so a
 * locale switch updates labels reactively.
 */

import type { Condition, Seasonal, ContainerType } from '$lib/types';

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

// Order matches a sensible visual sequence (most → least common).
export const CONTAINER_TYPES: ContainerType[] = [
	'box',
	'drawer',
	'shelf',
	'cabinet',
	'closet',
	'bin',
	'basket',
	'other'
];

export const CONTAINER_TYPE_KEYS: Record<ContainerType, string> = {
	box: 'containers.types.box',
	drawer: 'containers.types.drawer',
	shelf: 'containers.types.shelf',
	cabinet: 'containers.types.cabinet',
	closet: 'containers.types.closet',
	bin: 'containers.types.bin',
	basket: 'containers.types.basket',
	other: 'containers.types.other'
};
