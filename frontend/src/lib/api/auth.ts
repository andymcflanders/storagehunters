/**
 * Authentication API functions.
 */

import { get, post } from './client';
import type { User, SessionResponse } from '$lib/types';

export async function login(userId: string, password?: string): Promise<SessionResponse> {
	return post<SessionResponse>('/auth/login', {
		user_id: userId,
		password
	});
}

export async function loginByEmail(email: string, password: string): Promise<SessionResponse> {
	return post<SessionResponse>('/auth/login', {
		email,
		password
	});
}

export async function logout(): Promise<void> {
	await post('/auth/logout');
}

export async function getCurrentUser(): Promise<User> {
	return get<User>('/auth/me');
}
