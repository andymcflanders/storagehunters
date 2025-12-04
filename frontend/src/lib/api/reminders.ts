/**
 * Reminders API client.
 */

import { apiClient } from './client';

export type ReminderType = 'check_item' | 'expiration' | 'maintenance' | 'restock' | 'custom';

export interface Reminder {
	id: string;
	title: string;
	description: string | null;
	reminder_type: ReminderType;
	due_date: string;
	is_completed: boolean;
	is_recurring: boolean;
	recurrence_days: number | null;
	completed_at: string | null;
	created_at: string;
	item_id: string | null;
	item_name: string | null;
	container_id: string | null;
	container_name: string | null;
	is_overdue: boolean;
}

export interface ReminderListResponse {
	items: Reminder[];
	total: number;
	overdue_count: number;
	upcoming_count: number;
}

export interface CreateReminderRequest {
	title: string;
	description?: string | null;
	reminder_type?: ReminderType;
	due_date: string;
	item_id?: string | null;
	container_id?: string | null;
	is_recurring?: boolean;
	recurrence_days?: number | null;
}

export interface UpdateReminderRequest {
	title?: string;
	description?: string | null;
	reminder_type?: ReminderType;
	due_date?: string;
	is_recurring?: boolean;
	recurrence_days?: number | null;
}

export interface ReminderFilters {
	include_completed?: boolean;
	item_id?: string;
	container_id?: string;
	upcoming_days?: number;
}

export async function createReminder(data: CreateReminderRequest): Promise<Reminder> {
	const response = await apiClient('/api/reminders', {
		method: 'POST',
		body: JSON.stringify(data)
	});
	return response.json();
}

export async function listReminders(filters: ReminderFilters = {}): Promise<ReminderListResponse> {
	const params = new URLSearchParams();
	if (filters.include_completed) params.set('include_completed', 'true');
	if (filters.item_id) params.set('item_id', filters.item_id);
	if (filters.container_id) params.set('container_id', filters.container_id);
	if (filters.upcoming_days) params.set('upcoming_days', filters.upcoming_days.toString());

	const url = params.toString() ? `/api/reminders?${params}` : '/api/reminders';
	const response = await apiClient(url);
	return response.json();
}

export async function getUpcomingReminders(days: number = 7): Promise<ReminderListResponse> {
	const response = await apiClient(`/api/reminders/upcoming?days=${days}`);
	return response.json();
}

export async function getReminder(id: string): Promise<Reminder> {
	const response = await apiClient(`/api/reminders/${id}`);
	return response.json();
}

export async function updateReminder(id: string, data: UpdateReminderRequest): Promise<Reminder> {
	const response = await apiClient(`/api/reminders/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
	return response.json();
}

export async function completeReminder(id: string): Promise<Reminder> {
	const response = await apiClient(`/api/reminders/${id}/complete`, {
		method: 'POST'
	});
	return response.json();
}

export async function deleteReminder(id: string): Promise<void> {
	await apiClient(`/api/reminders/${id}`, {
		method: 'DELETE'
	});
}
