/**
 * Authentication store.
 */

import { writable, derived } from 'svelte/store';
import type { User } from '$lib/types';
import * as authApi from '$lib/api/auth';

function createAuthStore() {
	const { subscribe, set, update } = writable<{
		user: User | null;
		loading: boolean;
		initialized: boolean;
	}>({
		user: null,
		loading: false,
		initialized: false
	});

	return {
		subscribe,

		async initialize() {
			update((state) => ({ ...state, loading: true }));
			try {
				const user = await authApi.getCurrentUser();
				set({ user, loading: false, initialized: true });
			} catch {
				set({ user: null, loading: false, initialized: true });
			}
		},

		async login(userId: string, password?: string) {
			update((state) => ({ ...state, loading: true }));
			try {
				const session = await authApi.login(userId, password);
				set({ user: session.user, loading: false, initialized: true });
				return session;
			} catch (error) {
				update((state) => ({ ...state, loading: false }));
				throw error;
			}
		},

		async loginByEmail(email: string, password: string) {
			update((state) => ({ ...state, loading: true }));
			try {
				const session = await authApi.loginByEmail(email, password);
				set({ user: session.user, loading: false, initialized: true });
				return session;
			} catch (error) {
				update((state) => ({ ...state, loading: false }));
				throw error;
			}
		},

		async logout() {
			update((state) => ({ ...state, loading: true }));
			try {
				await authApi.logout();
			} finally {
				set({ user: null, loading: false, initialized: true });
			}
		},

		setUser(user: User | null) {
			update((state) => ({ ...state, user }));
		}
	};
}

export const auth = createAuthStore();
export const user = derived(auth, ($auth) => $auth.user);
export const isAuthenticated = derived(auth, ($auth) => $auth.user !== null);
export const isLoading = derived(auth, ($auth) => $auth.loading);
