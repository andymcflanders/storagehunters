/**
 * Backup API client.
 */

import { get, post, del, upload } from './client';

export interface BackupConfig {
	id: string;
	name: string;
	description: string | null;
	provider_type: string;
	include_images: boolean;
	encryption_enabled: boolean;
	compression_level: number;
	retention_count: number;
	is_active: boolean;
	is_default: boolean;
	created_at: string;
	updated_at: string;
}

export interface BackupHistory {
	id: string;
	config_id: string | null;
	filename: string;
	file_path: string | null;
	remote_id: string | null;
	size_bytes: number;
	checksum: string | null;
	status: string;
	error_message: string | null;
	started_at: string | null;
	completed_at: string | null;
	statistics: Record<string, unknown> | null;
}

export interface BackupHistoryListResponse {
	items: BackupHistory[];
	total: number;
	page: number;
	page_size: number;
}

export interface BackupTriggerRequest {
	include_images?: boolean;
	include_users?: boolean;
	compression_level?: number;
}

export interface BackupTriggerResponse {
	backup_id: string;
	status: string;
	message: string;
}

export interface BackupPreview {
	valid: boolean;
	version: string | null;
	created_at: string | null;
	statistics: Record<string, number> | null;
	error_message: string | null;
}

export interface RestoreRequest {
	restore_images?: boolean;
}

export interface RestoreResponse {
	success: boolean;
	message: string;
	statistics: Record<string, number> | null;
}

export interface BackupListFilters {
	page?: number;
	page_size?: number;
	status_filter?: string;
}

// Storage Provider types
export interface ProviderStatus {
	google_drive_available: boolean;
	dropbox_available: boolean;
	local_available: boolean;
}

export interface SharedDriveInfo {
	id: string;
	name: string;
}

export interface GoogleDriveTestResponse {
	success: boolean;
	message: string;
	email: string | null;
	shared_drives?: SharedDriveInfo[];
	has_shared_drives?: boolean;
}

export interface RemoteBackup {
	remote_id: string;
	filename: string;
	remote_path: string;
	size_bytes: number;
	created_at: string;
	checksum: string | null;
}

export interface RemoteBackupListResponse {
	success: boolean;
	backups: RemoteBackup[];
	error_message: string | null;
}

export interface UploadToProviderResponse {
	success: boolean;
	message: string;
	remote_id: string | null;
	remote_path: string | null;
}

// Schedule types
export interface BackupSchedule {
	id: string;
	config_id: string;
	name: string;
	frequency: 'daily' | 'weekly' | 'monthly';
	time_of_day: string;
	day_of_week: number | null;
	day_of_month: number | null;
	is_active: boolean;
	last_run_at: string | null;
	next_run_at: string | null;
	created_at: string;
}

export interface ScheduleCreateRequest {
	config_id: string;
	name: string;
	frequency: string;
	time_of_day: string;
	day_of_week?: number;
	day_of_month?: number;
	is_active?: boolean;
}

export interface ScheduleUpdateRequest {
	name?: string;
	frequency?: string;
	time_of_day?: string;
	day_of_week?: number;
	day_of_month?: number;
	is_active?: boolean;
}

// Backup History
export async function listBackupHistory(filters: BackupListFilters = {}): Promise<BackupHistoryListResponse> {
	const params = new URLSearchParams();
	if (filters.page) params.set('page', filters.page.toString());
	if (filters.page_size) params.set('page_size', filters.page_size.toString());
	if (filters.status_filter) params.set('status_filter', filters.status_filter);

	const url = params.toString() ? `/admin/backup/history?${params}` : '/admin/backup/history';
	return get<BackupHistoryListResponse>(url);
}

export async function getBackupHistory(backupId: string): Promise<BackupHistory> {
	return get<BackupHistory>(`/admin/backup/history/${backupId}`);
}

export async function deleteBackup(backupId: string): Promise<void> {
	return del(`/admin/backup/history/${backupId}`);
}

// Backup Operations
export async function triggerBackup(options: BackupTriggerRequest = {}): Promise<BackupTriggerResponse> {
	return post<BackupTriggerResponse>('/admin/backup/create', options);
}

export function getDownloadUrl(backupId: string): string {
	return `/api/admin/backup/history/${backupId}/download`;
}

export function getQuickDownloadUrl(includeImages: boolean = false): string {
	return `/api/admin/backup/quick-download?include_images=${includeImages}`;
}

// Restore Operations
export async function uploadForRestore(file: File): Promise<BackupPreview> {
	return upload<BackupPreview>('/admin/backup/restore/upload', file);
}

export async function executeRestore(options: RestoreRequest = {}): Promise<RestoreResponse> {
	return post<RestoreResponse>('/admin/backup/restore/execute', options);
}

export async function restoreFromHistory(backupId: string, options: RestoreRequest = {}): Promise<RestoreResponse> {
	return post<RestoreResponse>(`/admin/backup/restore/from-history/${backupId}`, options);
}

// Backup Configs
export async function listBackupConfigs(): Promise<BackupConfig[]> {
	return get<BackupConfig[]>('/admin/backup/configs');
}

export async function createBackupConfig(data: Partial<BackupConfig>): Promise<BackupConfig> {
	return post<BackupConfig>('/admin/backup/configs', data);
}

export async function deleteBackupConfig(configId: string): Promise<void> {
	return del(`/admin/backup/configs/${configId}`);
}

// Utility functions
export function formatBytes(bytes: number): string {
	if (bytes === 0) return '0 B';
	const k = 1024;
	const sizes = ['B', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function getStatusColor(status: string): string {
	switch (status) {
		case 'completed':
			return 'bg-green-100 text-green-800';
		case 'in_progress':
		case 'pending':
			return 'bg-blue-100 text-blue-800';
		case 'failed':
			return 'bg-red-100 text-red-800';
		default:
			return 'bg-slate-100 text-slate-800';
	}
}

// Storage Provider Operations
export async function getProviderStatus(): Promise<ProviderStatus> {
	return get<ProviderStatus>('/admin/backup/providers/status');
}

export async function testGoogleDriveCredentials(serviceAccountJson: string): Promise<GoogleDriveTestResponse> {
	return post<GoogleDriveTestResponse>('/admin/backup/providers/google-drive/test', {
		service_account_json: serviceAccountJson
	});
}

export async function listGoogleDriveBackups(serviceAccountJson: string): Promise<RemoteBackupListResponse> {
	return post<RemoteBackupListResponse>('/admin/backup/providers/google-drive/list', {
		service_account_json: serviceAccountJson
	});
}

export async function uploadToGoogleDrive(
	backupId: string,
	serviceAccountJson: string
): Promise<UploadToProviderResponse> {
	return post<UploadToProviderResponse>('/admin/backup/providers/upload', {
		backup_id: backupId,
		provider_type: 'google_drive',
		provider_config: {
			service_account_json: serviceAccountJson
		}
	});
}

export async function deleteFromGoogleDrive(
	remoteId: string,
	serviceAccountJson: string
): Promise<{ success: boolean; message: string }> {
	return del(`/admin/backup/providers/google-drive/${remoteId}`, {
		service_account_json: serviceAccountJson
	});
}

// Dropbox types
export interface DropboxTestResponse {
	success: boolean;
	message: string;
	email: string | null;
	account_name: string | null;
}

// Dropbox Operations
export async function testDropboxCredentials(accessToken: string): Promise<DropboxTestResponse> {
	return post<DropboxTestResponse>('/admin/backup/providers/dropbox/test', {
		access_token: accessToken
	});
}

export async function listDropboxBackups(accessToken: string): Promise<RemoteBackupListResponse> {
	return post<RemoteBackupListResponse>('/admin/backup/providers/dropbox/list', {
		access_token: accessToken
	});
}

export async function uploadToDropbox(
	backupId: string,
	accessToken: string
): Promise<UploadToProviderResponse> {
	return post<UploadToProviderResponse>('/admin/backup/providers/upload', {
		backup_id: backupId,
		provider_type: 'dropbox',
		provider_config: {
			access_token: accessToken
		}
	});
}

export async function deleteFromDropbox(
	remoteId: string,
	accessToken: string
): Promise<{ success: boolean; message: string }> {
	return del(`/admin/backup/providers/dropbox/${encodeURIComponent(remoteId)}`, {
		access_token: accessToken
	});
}

// Schedule Operations
export async function listSchedules(): Promise<BackupSchedule[]> {
	return get<BackupSchedule[]>('/admin/backup/schedules');
}

export async function createSchedule(data: ScheduleCreateRequest): Promise<BackupSchedule> {
	return post<BackupSchedule>('/admin/backup/schedules', data);
}

export async function updateSchedule(
	scheduleId: string,
	data: ScheduleUpdateRequest
): Promise<BackupSchedule> {
	return post<BackupSchedule>(`/admin/backup/schedules/${scheduleId}`, data);
}

export async function deleteSchedule(scheduleId: string): Promise<void> {
	return del(`/admin/backup/schedules/${scheduleId}`);
}

export async function triggerSchedule(scheduleId: string): Promise<BackupTriggerResponse> {
	return post<BackupTriggerResponse>(`/admin/backup/schedules/${scheduleId}/run`, {});
}

// Helper functions for schedules
export function getFrequencyLabel(frequency: string): string {
	switch (frequency) {
		case 'daily':
			return 'Daily';
		case 'weekly':
			return 'Weekly';
		case 'monthly':
			return 'Monthly';
		default:
			return frequency;
	}
}

export function getDayOfWeekLabel(day: number): string {
	const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
	return days[day] || `Day ${day}`;
}

export function formatScheduleDescription(schedule: BackupSchedule): string {
	let desc = `${getFrequencyLabel(schedule.frequency)} at ${schedule.time_of_day}`;
	if (schedule.frequency === 'weekly' && schedule.day_of_week !== null) {
		desc += ` on ${getDayOfWeekLabel(schedule.day_of_week)}`;
	} else if (schedule.frequency === 'monthly' && schedule.day_of_month !== null) {
		desc += ` on day ${schedule.day_of_month}`;
	}
	return desc;
}
