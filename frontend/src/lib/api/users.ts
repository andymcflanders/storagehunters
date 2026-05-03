/**
 * Users API functions.
 */

import { get, post, patch, del, upload } from './client';
import type { User, UserCreate, UserUpdate } from '$lib/types';

export async function listUsers(options?: { includeAdmins?: boolean }): Promise<User[]> {
	if (options?.includeAdmins === false) {
		return get<User[]>('/users?include_admins=false');
	}
	return get<User[]>('/users');
}

export async function createUser(data: UserCreate): Promise<User> {
	return post<User>('/users', data);
}

export async function getUser(id: string): Promise<User> {
	return get<User>(`/users/${id}`);
}

export async function updateUser(id: string, data: UserUpdate): Promise<User> {
	return patch<User>(`/users/${id}`, data);
}

export async function deleteUser(id: string): Promise<void> {
	return del(`/users/${id}`);
}

export async function uploadAvatar(id: string, file: File): Promise<User> {
	return upload<User>(`/users/${id}/avatar`, file);
}
