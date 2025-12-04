/**
 * API client for StorageHub backend.
 */

const API_BASE = '/api';

export class ApiError extends Error {
	constructor(
		public status: number,
		public statusText: string,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const errorData = await response.json().catch(() => ({}));
		throw new ApiError(
			response.status,
			response.statusText,
			errorData.detail || response.statusText
		);
	}

	// Handle 204 No Content
	if (response.status === 204) {
		return undefined as T;
	}

	return response.json();
}

export async function get<T>(endpoint: string): Promise<T> {
	const response = await fetch(`${API_BASE}${endpoint}`, {
		credentials: 'include'
	});
	return handleResponse<T>(response);
}

export async function post<T>(endpoint: string, data?: unknown): Promise<T> {
	const response = await fetch(`${API_BASE}${endpoint}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: data ? JSON.stringify(data) : undefined
	});
	return handleResponse<T>(response);
}

export async function patch<T>(endpoint: string, data: unknown): Promise<T> {
	const response = await fetch(`${API_BASE}${endpoint}`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify(data)
	});
	return handleResponse<T>(response);
}

export async function del<T>(endpoint: string): Promise<T> {
	const response = await fetch(`${API_BASE}${endpoint}`, {
		method: 'DELETE',
		credentials: 'include'
	});
	return handleResponse<T>(response);
}

export async function upload<T>(endpoint: string, file: File): Promise<T> {
	const formData = new FormData();
	formData.append('file', file);

	const response = await fetch(`${API_BASE}${endpoint}`, {
		method: 'POST',
		credentials: 'include',
		body: formData
	});
	return handleResponse<T>(response);
}
