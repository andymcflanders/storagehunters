<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { admin, ssl, backup } from '$lib/api';
	import { Card, Button, Input } from '$lib/components';
	import type { SystemStats, AdminUser, ActivityLogItem, OpenAISettings } from '$lib/api/admin';
	import type { SSLStatus, SSLMode } from '$lib/api/ssl';
	import type { BackupHistory, BackupPreview, ProviderStatus, RemoteBackup, BackupSchedule } from '$lib/api/backup';

	type Tab = 'dashboard' | 'users' | 'activity' | 'ssl' | 'ai' | 'backups';

	let activeTab: Tab = 'dashboard';
	let stats: SystemStats | null = null;
	let users: AdminUser[] = [];
	let usersTotal = 0;
	let usersPage = 1;
	let activityLogs: ActivityLogItem[] = [];
	let activityTotal = 0;
	let activityPage = 1;
	let loading = true;
	let loadingUsers = false;
	let loadingActivity = false;

	// User modal state
	let showUserModal = false;
	let editingUser: AdminUser | null = null;
	let userFormData = {
		name: '',
		email: '',
		role: 'user' as 'admin' | 'user',
		requires_password: false,
		password: '',
		is_active: true,
		is_profile: false,
		birthdate: '' as string,
		gender: '' as '' | 'male' | 'female' | 'other'
	};
	let savingUser = false;

	// Filters
	let userSearch = '';
	let userRoleFilter = '';
	let userActiveFilter = '';

	// SSL state
	let sslStatus: SSLStatus | null = null;
	let loadingSSL = false;
	let generatingCert = false;
	let sslFormData = {
		mode: 'disabled' as SSLMode,
		domain: '',
		email: ''
	};

	// AI loading state (shared between OpenAI panel and tab loader)
	let loadingAI = false;
	let recomputingSizeAges = false;

	// OpenAI settings state
	let openaiSettings: OpenAISettings | null = null;
	let savingOpenAI = false;
	let openaiFormData = {
		vision_enabled: true,
		vision_model: 'gpt-4o',
		vision_max_tokens: 500,
		vision_temperature: 0.3,
		summary_enabled: true,
		summary_model: 'gpt-4o-mini',
		summary_max_tokens: 150,
		summary_temperature: 0.3,
		owner_suggestion_enabled: true
	};

	// Live cost estimates that recompute reactively from the form so
	// the user sees the impact of moving sliders / picking a different
	// model without needing to save first. Output tokens = the
	// max_tokens cap, framed as "worst-case cost per call" — that
	// matches the user's mental model ("more tokens = more expensive")
	// even though typical generations use much less than the cap.
	$: visionLiveCost = (() => {
		if (!openaiSettings) return null;
		const m = openaiSettings.vision_models.find((x) => x.id === openaiFormData.vision_model);
		if (!m) return null;
		const inputTokens = 600 + 1000; // ~600 prompt + ~1000 per image, 1 image
		const outputTokens = openaiFormData.vision_max_tokens;
		const inputPrice = m.vision_input_price_per_1m ?? m.input_price_per_1m;
		const cost = (inputTokens * inputPrice + outputTokens * m.output_price_per_1m) / 1_000_000;
		return { inputTokens, outputTokens, cost };
	})();

	$: summaryLiveCost = (() => {
		if (!openaiSettings) return null;
		const m = openaiSettings.text_models.find((x) => x.id === openaiFormData.summary_model);
		if (!m) return null;
		const inputTokens = 400; // rough container summary prompt
		const outputTokens = openaiFormData.summary_max_tokens;
		const cost = (inputTokens * m.input_price_per_1m + outputTokens * m.output_price_per_1m) / 1_000_000;
		return { inputTokens, outputTokens, cost };
	})();

	// Language settings — which languages the AI generates content in.
	let languageSettings: { supported_languages: string[]; default_language: string } | null = null;
	let savingLanguages = false;
	let newLanguageInput = '';

	// Backup state
	let backups: BackupHistory[] = [];
	let backupsTotal = 0;
	let backupsPage = 1;
	let loadingBackups = false;
	let creatingBackup = false;
	let restoringBackup = false;
	let showRestoreModal = false;
	let restorePreview: BackupPreview | null = null;
	let restoreFile: File | null = null;
	let backupOptions = {
		include_images: false,
		include_users: false
	};
	let restoreOptions = {
		restore_images: true
	};

	// Google Drive state
	let providerStatus: ProviderStatus | null = null;
	let googleDriveCredentials = '';
	let googleDriveEmail = '';
	let googleDriveConnected = false;
	let testingGoogleDrive = false;
	let loadingRemoteBackups = false;
	let remoteBackups: RemoteBackup[] = [];
	let uploadingToGoogleDrive = false;

	// Dropbox state
	let dropboxAccessToken = '';
	let dropboxEmail = '';
	let dropboxAccountName = '';
	let dropboxConnected = false;
	let testingDropbox = false;
	let loadingDropboxBackups = false;
	let dropboxBackups: RemoteBackup[] = [];
	let uploadingToDropbox = false;

	// Schedule state
	let schedules: BackupSchedule[] = [];
	let loadingSchedules = false;
	let showScheduleModal = false;
	let editingSchedule: BackupSchedule | null = null;
	let savingSchedule = false;
	let scheduleFormData = {
		name: '',
		frequency: 'daily' as 'daily' | 'weekly' | 'monthly',
		time_of_day: '02:00',
		day_of_week: 0,
		day_of_month: 1,
		is_active: true
	};

	const tabs: { id: Tab; label: string; icon: string }[] = [
		{ id: 'dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
		{ id: 'users', label: 'Users', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
		{ id: 'activity', label: 'Activity Logs', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
		{ id: 'ssl', label: 'SSL/HTTPS', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
		{ id: 'ai', label: 'AI Settings', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
		{ id: 'backups', label: 'Backups', icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12' }
	];

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}

		// Check if user is admin
		if ($user.role !== 'admin') {
			toast.error('Admin access required');
			goto('/');
			return;
		}

		await loadStats();
	});

	async function loadStats() {
		loading = true;
		try {
			stats = await admin.getSystemStats();
		} catch (error) {
			toast.error('Failed to load stats');
		} finally {
			loading = false;
		}
	}

	async function loadUsers() {
		loadingUsers = true;
		try {
			const filters: admin.UserListFilters = {
				page: usersPage,
				page_size: 20,
				search: userSearch || undefined,
				role: userRoleFilter as 'admin' | 'user' || undefined,
				is_active: userActiveFilter === '' ? undefined : userActiveFilter === 'true'
			};
			const response = await admin.listUsers(filters);
			users = response.items;
			usersTotal = response.total;
		} catch (error) {
			toast.error('Failed to load users');
		} finally {
			loadingUsers = false;
		}
	}

	async function loadActivity() {
		loadingActivity = true;
		try {
			const response = await admin.getActivityLogs({
				page: activityPage,
				page_size: 50,
				days: 30
			});
			activityLogs = response.items;
			activityTotal = response.total;
		} catch (error) {
			toast.error('Failed to load activity logs');
		} finally {
			loadingActivity = false;
		}
	}

	function setActiveTab(tabId: string) {
		activeTab = tabId as Tab;
		if (tabId === 'users' && users.length === 0) {
			loadUsers();
		} else if (tabId === 'activity' && activityLogs.length === 0) {
			loadActivity();
		} else if (tabId === 'ssl' && !sslStatus) {
			loadSSLStatus();
		} else if (tabId === 'ai' && !openaiSettings) {
			loadAISettings();
		} else if (tabId === 'backups' && backups.length === 0) {
			loadBackups();
		}
	}

	async function loadSSLStatus() {
		loadingSSL = true;
		try {
			sslStatus = await ssl.getSSLStatus();
			sslFormData.mode = sslStatus.mode;
			sslFormData.domain = sslStatus.domain || '';
		} catch (error) {
			toast.error('Failed to load SSL status');
		} finally {
			loadingSSL = false;
		}
	}

	async function handleGenerateCertificate() {
		if (sslFormData.mode === 'letsencrypt') {
			if (!sslFormData.domain.trim()) {
				toast.warning('Domain is required for Let\'s Encrypt');
				return;
			}
			if (!sslFormData.email.trim()) {
				toast.warning('Email is required for Let\'s Encrypt');
				return;
			}
		}

		generatingCert = true;
		try {
			const result = await ssl.generateCertificate({
				mode: sslFormData.mode,
				domain: sslFormData.domain || null,
				email: sslFormData.email || null
			});

			if (result.success) {
				toast.success(result.message);
				await loadSSLStatus();
				// Notify user to restart if enabling/disabling SSL
				if (sslFormData.mode !== 'disabled') {
					toast.info('HTTPS is now enabled. You may need to access the site via https://');
				}
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to generate certificate';
			toast.error(message);
		} finally {
			generatingCert = false;
		}
	}

	async function handleRenewCertificate() {
		generatingCert = true;
		try {
			const result = await ssl.renewCertificate();
			if (result.success) {
				toast.success(result.message);
				await loadSSLStatus();
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to renew certificate';
			toast.error(message);
		} finally {
			generatingCert = false;
		}
	}

	async function handleTestCertificate() {
		try {
			const result = await ssl.testCertificate();
			if (result.success) {
				toast.success(result.message);
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to test certificate';
			toast.error(message);
		}
	}

	function getSSLModeLabel(mode: SSLMode): string {
		switch (mode) {
			case 'disabled':
				return 'Disabled (HTTP only)';
			case 'self_signed':
				return 'Self-Signed Certificate';
			case 'letsencrypt':
				return "Let's Encrypt";
			default:
				return mode;
		}
	}

	async function loadAISettings() {
		loadingAI = true;
		try {
			openaiSettings = await admin.getOpenAISettings();
			openaiFormData = {
				vision_enabled: openaiSettings.vision_enabled,
				vision_model: openaiSettings.vision_model,
				vision_max_tokens: openaiSettings.vision_max_tokens,
				vision_temperature: openaiSettings.vision_temperature,
				summary_enabled: openaiSettings.summary_enabled,
				summary_model: openaiSettings.summary_model,
				summary_max_tokens: openaiSettings.summary_max_tokens,
				summary_temperature: openaiSettings.summary_temperature,
				owner_suggestion_enabled: openaiSettings.owner_suggestion_enabled ?? true
			};
			languageSettings = await admin.getLanguageSettings();
		} catch (error) {
			toast.error('Failed to load AI settings');
		} finally {
			loadingAI = false;
		}
	}

	async function addLanguage() {
		if (!languageSettings) return;
		const code = newLanguageInput.trim().toLowerCase();
		if (!code) return;
		if (languageSettings.supported_languages.includes(code)) {
			toast.error(`${code} is already enabled`);
			return;
		}
		await saveLanguages({
			supported_languages: [...languageSettings.supported_languages, code]
		});
		newLanguageInput = '';
	}

	async function removeLanguage(code: string) {
		if (!languageSettings) return;
		if (languageSettings.supported_languages.length <= 1) {
			toast.error('At least one language is required');
			return;
		}
		const next = languageSettings.supported_languages.filter((c) => c !== code);
		const update: admin.LanguageSettingsUpdate = { supported_languages: next };
		if (languageSettings.default_language === code) {
			update.default_language = next[0];
		}
		await saveLanguages(update);
	}

	async function setDefaultLanguage(code: string) {
		await saveLanguages({ default_language: code });
	}

	async function saveLanguages(update: admin.LanguageSettingsUpdate) {
		savingLanguages = true;
		try {
			languageSettings = await admin.updateLanguageSettings(update);
			toast.success('Languages saved');
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to save languages';
			toast.error(message);
		} finally {
			savingLanguages = false;
		}
	}

	async function handleSaveOpenAISettings() {
		savingOpenAI = true;
		try {
			const updateData: admin.OpenAISettingsUpdate = {
				vision_enabled: openaiFormData.vision_enabled,
				vision_model: openaiFormData.vision_model,
				vision_max_tokens: openaiFormData.vision_max_tokens,
				vision_temperature: openaiFormData.vision_temperature,
				summary_enabled: openaiFormData.summary_enabled,
				summary_model: openaiFormData.summary_model,
				summary_max_tokens: openaiFormData.summary_max_tokens,
				summary_temperature: openaiFormData.summary_temperature,
				owner_suggestion_enabled: openaiFormData.owner_suggestion_enabled
			};

			openaiSettings = await admin.updateOpenAISettings(updateData);
			toast.success('OpenAI settings saved');
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to save settings';
			toast.error(message);
		} finally {
			savingOpenAI = false;
		}
	}

	async function handleRecomputeSizeAges() {
		recomputingSizeAges = true;
		try {
			const result = await admin.recomputeSizeAges();
			if (result.queued === 0) {
				toast.info('Nothing to backfill — every item with a size already has an age range.');
			} else {
				toast.success(`Queued backfill for ${result.queued} item${result.queued === 1 ? '' : 's'}. Refresh /outgrown in a minute.`);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to queue backfill';
			toast.error(message);
		} finally {
			recomputingSizeAges = false;
		}
	}

	function openCreateUserModal() {
		editingUser = null;
		userFormData = {
			name: '',
			email: '',
			role: 'user',
			requires_password: false,
			password: '',
			is_active: true,
			is_profile: false,
			birthdate: '',
			gender: ''
		};
		showUserModal = true;
	}

	function openEditUserModal(u: AdminUser) {
		editingUser = u;
		userFormData = {
			name: u.name,
			email: u.email || '',
			role: u.role,
			requires_password: u.requires_password,
			password: '',
			is_active: u.is_active,
			is_profile: u.is_profile ?? false,
			birthdate: u.birthdate || '',
			gender: (u.gender ?? '') as '' | 'male' | 'female' | 'other'
		};
		showUserModal = true;
	}

	async function handleSaveUser() {
		if (!userFormData.name.trim()) {
			toast.warning('Please enter a name');
			return;
		}

		savingUser = true;
		try {
			if (editingUser) {
				const updateData: admin.UpdateUserRequest = {
					name: userFormData.name,
					email: userFormData.email || null,
					role: userFormData.role,
					requires_password: userFormData.requires_password,
					is_active: userFormData.is_active,
					is_profile: userFormData.is_profile,
					birthdate: userFormData.birthdate || null,
					gender: userFormData.gender || null
				};
				if (userFormData.password) {
					updateData.password = userFormData.password;
				}
				await admin.updateUser(editingUser.id, updateData);
				toast.success('User updated');
			} else {
				await admin.createUser({
					name: userFormData.name,
					email: userFormData.email || null,
					role: userFormData.role,
					requires_password: userFormData.requires_password,
					password: userFormData.password || null,
					is_profile: userFormData.is_profile,
					birthdate: userFormData.birthdate || null,
					gender: userFormData.gender || null
				});
				toast.success('User created');
			}
			showUserModal = false;
			await loadUsers();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to save user';
			toast.error(message);
		} finally {
			savingUser = false;
		}
	}

	async function handleDeleteUser(u: AdminUser) {
		if (!confirm(`Delete user "${u.name}"? This cannot be undone.`)) return;

		try {
			await admin.deleteUser(u.id);
			toast.success('User deleted');
			await loadUsers();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to delete user';
			toast.error(message);
		}
	}

	async function handleToggleUserActive(u: AdminUser) {
		try {
			await admin.updateUser(u.id, { is_active: !u.is_active });
			toast.success(u.is_active ? 'User deactivated' : 'User activated');
			await loadUsers();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to update user';
			toast.error(message);
		}
	}

	function handleSearchUsers() {
		usersPage = 1;
		loadUsers();
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatDateTime(dateStr: string): string {
		return new Date(dateStr).toLocaleString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getActionColor(action: string): string {
		switch (action) {
			case 'created':
				return 'bg-green-100 text-green-800';
			case 'updated':
				return 'bg-blue-100 text-blue-800';
			case 'deleted':
				return 'bg-red-100 text-red-800';
			case 'moved':
				return 'bg-yellow-100 text-yellow-800';
			default:
				return 'bg-slate-100 text-slate-800';
		}
	}

	// Backup functions
	async function loadBackups() {
		loadingBackups = true;
		try {
			const [historyResponse] = await Promise.all([
				backup.listBackupHistory({
					page: backupsPage,
					page_size: 20
				}),
				loadProviderStatus(),
				loadSchedules()
			]);
			backups = historyResponse.items;
			backupsTotal = historyResponse.total;
		} catch (error) {
			toast.error('Failed to load backups');
		} finally {
			loadingBackups = false;
		}
	}

	async function handleCreateBackup() {
		creatingBackup = true;
		try {
			const result = await backup.triggerBackup({
				include_images: backupOptions.include_images,
				include_users: backupOptions.include_users
			});
			toast.success(result.message);
			// Poll for completion
			setTimeout(loadBackups, 2000);
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to create backup';
			toast.error(message);
		} finally {
			creatingBackup = false;
		}
	}

	function handleQuickDownload() {
		const url = backup.getQuickDownloadUrl(backupOptions.include_images);
		window.location.href = url;
	}

	function handleDownloadBackup(b: BackupHistory) {
		window.location.href = backup.getDownloadUrl(b.id);
	}

	async function handleDeleteBackup(b: BackupHistory) {
		if (!confirm(`Delete backup "${b.filename}"? This cannot be undone.`)) return;

		try {
			await backup.deleteBackup(b.id);
			toast.success('Backup deleted');
			await loadBackups();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to delete backup';
			toast.error(message);
		}
	}

	async function handleRestoreFromHistory(b: BackupHistory) {
		if (!confirm(`Restore from "${b.filename}"? This will merge data from this backup into your current database.`)) return;

		restoringBackup = true;
		try {
			const result = await backup.restoreFromHistory(b.id, {
				restore_images: restoreOptions.restore_images
			});
			if (result.success) {
				toast.success(result.message);
				if (result.statistics) {
					const stats = result.statistics;
					toast.info(`Restored: ${stats.locations_restored || 0} locations, ${stats.containers_restored || 0} containers, ${stats.items_restored || 0} items`);
				}
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Restore failed';
			toast.error(message);
		} finally {
			restoringBackup = false;
		}
	}

	async function handleFileUpload(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		if (!file.name.endsWith('.zip')) {
			toast.warning('Please select a .zip backup file');
			return;
		}

		restoreFile = file;
		restoringBackup = true;

		try {
			restorePreview = await backup.uploadForRestore(file);
			if (restorePreview.valid) {
				showRestoreModal = true;
			} else {
				toast.error(restorePreview.error_message || 'Invalid backup file');
				restorePreview = null;
				restoreFile = null;
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to process backup file';
			toast.error(message);
			restoreFile = null;
		} finally {
			restoringBackup = false;
			// Reset file input
			input.value = '';
		}
	}

	async function handleExecuteRestore() {
		if (!restorePreview) return;

		restoringBackup = true;
		try {
			const result = await backup.executeRestore({
				restore_images: restoreOptions.restore_images
			});

			if (result.success) {
				toast.success(result.message);
				if (result.statistics) {
					const stats = result.statistics;
					toast.info(`Restored: ${stats.locations_restored || 0} locations, ${stats.containers_restored || 0} containers, ${stats.items_restored || 0} items`);
				}
				showRestoreModal = false;
				restorePreview = null;
				restoreFile = null;
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Restore failed';
			toast.error(message);
		} finally {
			restoringBackup = false;
		}
	}

	function cancelRestore() {
		showRestoreModal = false;
		restorePreview = null;
		restoreFile = null;
	}

	// Google Drive functions
	async function loadProviderStatus() {
		try {
			providerStatus = await backup.getProviderStatus();
		} catch (error) {
			console.error('Failed to load provider status:', error);
		}
	}

	let googleDriveWarning = '';
	let googleDriveSharedDrives: backup.SharedDriveInfo[] = [];

	async function handleTestGoogleDrive() {
		if (!googleDriveCredentials.trim()) {
			toast.warning('Please paste your service account JSON credentials');
			return;
		}

		testingGoogleDrive = true;
		googleDriveWarning = '';
		googleDriveSharedDrives = [];
		try {
			const result = await backup.testGoogleDriveCredentials(googleDriveCredentials);
			if (result.success) {
				googleDriveEmail = result.email || '';
				googleDriveConnected = true;
				googleDriveSharedDrives = result.shared_drives || [];

				// Check if we have Shared Drives (required for uploads)
				if (!result.has_shared_drives) {
					googleDriveWarning = result.message;
					toast.warning('No Shared Drives found - uploads will not work');
				} else {
					toast.success(result.message);
					// Load remote backups
					await loadRemoteBackups();
				}
			} else {
				toast.error(result.message);
				googleDriveConnected = false;
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to test credentials';
			toast.error(message);
			googleDriveConnected = false;
		} finally {
			testingGoogleDrive = false;
		}
	}

	async function loadRemoteBackups() {
		if (!googleDriveCredentials || !googleDriveConnected) return;

		loadingRemoteBackups = true;
		try {
			const result = await backup.listGoogleDriveBackups(googleDriveCredentials);
			if (result.success) {
				remoteBackups = result.backups;
			} else {
				toast.error(result.error_message || 'Failed to list remote backups');
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to load remote backups';
			toast.error(message);
		} finally {
			loadingRemoteBackups = false;
		}
	}

	async function handleUploadToGoogleDrive(b: BackupHistory) {
		if (!googleDriveCredentials || !googleDriveConnected) {
			toast.warning('Please connect to Google Drive first');
			return;
		}

		uploadingToGoogleDrive = true;
		try {
			const result = await backup.uploadToGoogleDrive(b.id, googleDriveCredentials);
			if (result.success) {
				toast.success(result.message);
				await loadRemoteBackups();
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Upload failed';
			toast.error(message);
		} finally {
			uploadingToGoogleDrive = false;
		}
	}

	async function handleDeleteFromGoogleDrive(remoteId: string, filename: string) {
		if (!confirm(`Delete "${filename}" from Google Drive? This cannot be undone.`)) return;

		try {
			const result = await backup.deleteFromGoogleDrive(remoteId, googleDriveCredentials);
			if (result.success) {
				toast.success('Deleted from Google Drive');
				await loadRemoteBackups();
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Delete failed';
			toast.error(message);
		}
	}

	function disconnectGoogleDrive() {
		googleDriveCredentials = '';
		googleDriveEmail = '';
		googleDriveConnected = false;
		googleDriveWarning = '';
		googleDriveSharedDrives = [];
		remoteBackups = [];
	}

	// Dropbox functions
	async function handleTestDropbox() {
		if (!dropboxAccessToken.trim()) {
			toast.warning('Please enter your Dropbox access token');
			return;
		}

		testingDropbox = true;
		try {
			const result = await backup.testDropboxCredentials(dropboxAccessToken);
			if (result.success) {
				dropboxEmail = result.email || '';
				dropboxAccountName = result.account_name || '';
				dropboxConnected = true;
				toast.success(result.message);
				await loadDropboxBackups();
			} else {
				toast.error(result.message);
				dropboxConnected = false;
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to test credentials';
			toast.error(message);
			dropboxConnected = false;
		} finally {
			testingDropbox = false;
		}
	}

	async function loadDropboxBackups() {
		if (!dropboxAccessToken || !dropboxConnected) return;

		loadingDropboxBackups = true;
		try {
			const result = await backup.listDropboxBackups(dropboxAccessToken);
			if (result.success) {
				dropboxBackups = result.backups;
			} else {
				toast.error(result.error_message || 'Failed to list backups');
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to load backups';
			toast.error(message);
		} finally {
			loadingDropboxBackups = false;
		}
	}

	async function handleUploadToDropbox(b: BackupHistory) {
		if (!dropboxAccessToken || !dropboxConnected) {
			toast.error('Please connect to Dropbox first');
			return;
		}

		uploadingToDropbox = true;
		try {
			const result = await backup.uploadToDropbox(b.id, dropboxAccessToken);
			if (result.success) {
				toast.success('Backup uploaded to Dropbox');
				await loadDropboxBackups();
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Upload failed';
			toast.error(message);
		} finally {
			uploadingToDropbox = false;
		}
	}

	async function handleDeleteFromDropbox(remoteId: string) {
		try {
			const result = await backup.deleteFromDropbox(remoteId, dropboxAccessToken);
			if (result.success) {
				toast.success('Backup deleted from Dropbox');
				await loadDropboxBackups();
			} else {
				toast.error(result.message);
			}
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Delete failed';
			toast.error(message);
		}
	}

	function disconnectDropbox() {
		dropboxAccessToken = '';
		dropboxEmail = '';
		dropboxAccountName = '';
		dropboxConnected = false;
		dropboxBackups = [];
	}

	// Schedule functions
	async function loadSchedules() {
		loadingSchedules = true;
		try {
			schedules = await backup.listSchedules();
		} catch (error) {
			console.error('Failed to load schedules:', error);
		} finally {
			loadingSchedules = false;
		}
	}

	function openNewScheduleModal() {
		editingSchedule = null;
		scheduleFormData = {
			name: 'Daily Backup',
			frequency: 'daily',
			time_of_day: '02:00',
			day_of_week: 0,
			day_of_month: 1,
			is_active: true
		};
		showScheduleModal = true;
	}

	function openEditScheduleModal(schedule: BackupSchedule) {
		editingSchedule = schedule;
		scheduleFormData = {
			name: schedule.name,
			frequency: schedule.frequency,
			time_of_day: schedule.time_of_day,
			day_of_week: schedule.day_of_week ?? 0,
			day_of_month: schedule.day_of_month ?? 1,
			is_active: schedule.is_active
		};
		showScheduleModal = true;
	}

	async function handleSaveSchedule() {
		savingSchedule = true;
		try {
			if (editingSchedule) {
				// Update existing
				await backup.updateSchedule(editingSchedule.id, {
					name: scheduleFormData.name,
					frequency: scheduleFormData.frequency,
					time_of_day: scheduleFormData.time_of_day,
					day_of_week: scheduleFormData.frequency === 'weekly' ? scheduleFormData.day_of_week : undefined,
					day_of_month: scheduleFormData.frequency === 'monthly' ? scheduleFormData.day_of_month : undefined,
					is_active: scheduleFormData.is_active
				});
				toast.success('Schedule updated');
			} else {
				// Create new - need a config_id, we'll create a default local config
				// For simplicity, create schedule without config for now
				toast.error('Creating schedules requires a backup configuration. Please create one first.');
				savingSchedule = false;
				return;
			}
			showScheduleModal = false;
			await loadSchedules();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Failed to save schedule';
			toast.error(message);
		} finally {
			savingSchedule = false;
		}
	}

	async function handleDeleteSchedule(schedule: BackupSchedule) {
		if (!confirm(`Delete schedule "${schedule.name}"? This cannot be undone.`)) return;

		try {
			await backup.deleteSchedule(schedule.id);
			toast.success('Schedule deleted');
			await loadSchedules();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Delete failed';
			toast.error(message);
		}
	}

	async function handleToggleSchedule(schedule: BackupSchedule) {
		try {
			await backup.updateSchedule(schedule.id, {
				is_active: !schedule.is_active
			});
			toast.success(schedule.is_active ? 'Schedule paused' : 'Schedule activated');
			await loadSchedules();
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Update failed';
			toast.error(message);
		}
	}

	async function handleRunScheduleNow(schedule: BackupSchedule) {
		try {
			await backup.triggerSchedule(schedule.id);
			toast.success('Backup triggered');
			// Refresh history after a short delay
			setTimeout(() => loadBackups(), 2000);
		} catch (error: unknown) {
			const message = error instanceof Error ? error.message : 'Trigger failed';
			toast.error(message);
		}
	}
</script>

<svelte:head>
	<title>Admin Panel - StorageHub</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Admin Panel</h1>
		<p class="mt-1 text-slate-500 dark:text-slate-400">Manage users, view system stats, and monitor activity</p>
	</div>

	<!-- Tabs -->
	<div class="border-b border-slate-200 dark:border-slate-700">
		<nav class="-mb-px flex space-x-8">
			{#each tabs as tab}
				<button
					class="flex items-center gap-2 border-b-2 px-1 py-4 text-sm font-medium transition-colors
						{activeTab === tab.id
						? 'border-primary-500 text-primary-600'
						: 'border-transparent text-slate-500 dark:text-slate-400 hover:border-slate-300 hover:text-slate-700'}"
					on:click={() => setActiveTab(tab.id)}
				>
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={tab.icon} />
					</svg>
					{tab.label}
				</button>
			{/each}
		</nav>
	</div>

	<!-- Dashboard Tab -->
	{#if activeTab === 'dashboard'}
		{#if loading}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				{#each [1, 2, 3, 4] as _}
					<div class="h-24 animate-pulse rounded-xl bg-slate-200"></div>
				{/each}
			</div>
		{:else if stats}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<!-- Users Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600 dark:text-blue-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500 dark:text-slate-400">Total Users</p>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats.total_users}</p>
							<p class="text-xs text-slate-400">{stats.active_users} active, {stats.admin_users} admins</p>
						</div>
					</div>
				</Card>

				<!-- Locations Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 text-green-600 dark:text-green-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500 dark:text-slate-400">Locations</p>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats.total_locations}</p>
						</div>
					</div>
				</Card>

				<!-- Containers Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 text-purple-600 dark:text-purple-400">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500 dark:text-slate-400">Containers</p>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats.total_containers}</p>
						</div>
					</div>
				</Card>

				<!-- Items Card -->
				<Card>
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
							</svg>
						</div>
						<div>
							<p class="text-sm text-slate-500 dark:text-slate-400">Items</p>
							<p class="text-2xl font-bold text-slate-900 dark:text-white">{stats.total_items}</p>
							<p class="text-xs text-slate-400">+{stats.items_created_last_30_days} last 30 days</p>
						</div>
					</div>
				</Card>
			</div>

			<!-- Activity Summary -->
			<Card>
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Recent Activity</h3>
				<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
					{stats.recent_activity_count} actions in the last 30 days
				</p>
				<div class="mt-4">
					<Button variant="secondary" on:click={() => setActiveTab('activity')}>
						View All Activity
					</Button>
				</div>
			</Card>
		{/if}
	{/if}

	<!-- Users Tab -->
	{#if activeTab === 'users'}
		<div class="space-y-4">
			<!-- Toolbar -->
			<div class="flex flex-wrap items-center gap-4">
				<div class="flex-1">
					<form on:submit|preventDefault={handleSearchUsers} class="flex gap-2">
						<input
							type="text"
							bind:value={userSearch}
							placeholder="Search users..."
							class="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
						/>
						<Button type="submit" variant="secondary">Search</Button>
					</form>
				</div>
				<select
					bind:value={userRoleFilter}
					on:change={() => { usersPage = 1; loadUsers(); }}
					class="rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				>
					<option value="">All Roles</option>
					<option value="admin">Admin</option>
					<option value="user">User</option>
				</select>
				<select
					bind:value={userActiveFilter}
					on:change={() => { usersPage = 1; loadUsers(); }}
					class="rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
				>
					<option value="">All Status</option>
					<option value="true">Active</option>
					<option value="false">Inactive</option>
				</select>
				<Button on:click={openCreateUserModal}>
					<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					Add User
				</Button>
			</div>

			<!-- Users Table -->
			{#if loadingUsers}
				<div class="animate-pulse space-y-2">
					{#each [1, 2, 3, 4, 5] as _}
						<div class="h-16 rounded-lg bg-slate-200"></div>
					{/each}
				</div>
			{:else}
				<Card>
					<div class="overflow-x-auto">
						<table class="w-full">
							<thead>
								<tr class="border-b border-slate-200 dark:border-slate-700 text-left text-sm text-slate-500 dark:text-slate-400">
									<th class="pb-3 font-medium">User</th>
									<th class="pb-3 font-medium">Role</th>
									<th class="pb-3 font-medium">Status</th>
									<th class="pb-3 font-medium">Items</th>
									<th class="pb-3 font-medium">Created</th>
									<th class="pb-3 font-medium">Last Active</th>
									<th class="pb-3 font-medium">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-100">
								{#each users as u}
									<tr class="text-sm">
										<td class="py-3">
											<div>
												<p class="font-medium text-slate-900 dark:text-white">{u.name}</p>
												<p class="text-slate-500 dark:text-slate-400">{u.email || 'No email'}</p>
											</div>
										</td>
										<td class="py-3">
											<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
												{u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-100'}">
												{u.role}
											</span>
										</td>
										<td class="py-3">
											<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
												{u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800 dark:text-red-200'}">
												{u.is_active ? 'Active' : 'Inactive'}
											</span>
										</td>
										<td class="py-3 text-slate-600 dark:text-slate-400">{u.item_count}</td>
										<td class="py-3 text-slate-600 dark:text-slate-400">{formatDate(u.created_at)}</td>
										<td class="py-3 text-slate-600 dark:text-slate-400">
											{u.last_activity ? formatDate(u.last_activity) : 'Never'}
										</td>
										<td class="py-3">
											<div class="flex items-center gap-1">
												<button
													class="rounded p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
													title="Edit"
													on:click={() => openEditUserModal(u)}
												>
													<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
													</svg>
												</button>
												<button
													class="rounded p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
													title={u.is_active ? 'Deactivate' : 'Activate'}
													on:click={() => handleToggleUserActive(u)}
												>
													{#if u.is_active}
														<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
														</svg>
													{:else}
														<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
															<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
														</svg>
													{/if}
												</button>
												<button
													class="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
													title="Delete"
													on:click={() => handleDeleteUser(u)}
												>
													<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
												</button>
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>

					{#if users.length === 0}
						<div class="py-8 text-center text-slate-500 dark:text-slate-400">No users found</div>
					{/if}

					<!-- Pagination -->
					{#if usersTotal > 20}
						<div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Showing {(usersPage - 1) * 20 + 1} to {Math.min(usersPage * 20, usersTotal)} of {usersTotal} users
							</p>
							<div class="flex gap-2">
								<Button
									variant="secondary"
									size="sm"
									disabled={usersPage === 1}
									on:click={() => { usersPage--; loadUsers(); }}
								>
									Previous
								</Button>
								<Button
									variant="secondary"
									size="sm"
									disabled={usersPage * 20 >= usersTotal}
									on:click={() => { usersPage++; loadUsers(); }}
								>
									Next
								</Button>
							</div>
						</div>
					{/if}
				</Card>
			{/if}
		</div>
	{/if}

	<!-- Activity Tab -->
	{#if activeTab === 'activity'}
		<div class="space-y-4">
			{#if loadingActivity}
				<div class="animate-pulse space-y-2">
					{#each [1, 2, 3, 4, 5] as _}
						<div class="h-16 rounded-lg bg-slate-200"></div>
					{/each}
				</div>
			{:else}
				<Card>
					<div class="space-y-4">
						{#each activityLogs as log}
							<div class="flex items-start gap-4 border-b border-slate-100 pb-4 last:border-0 last:pb-0">
								<div class="flex-1">
									<div class="flex items-center gap-2">
										<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getActionColor(log.action)}">
											{log.action}
										</span>
										<span class="text-sm font-medium text-slate-900 dark:text-white">{log.entity_name}</span>
										<span class="text-sm text-slate-500 dark:text-slate-400">({log.entity_type})</span>
									</div>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										by {log.user_name || 'Unknown'} at {formatDateTime(log.created_at)}
									</p>
								</div>
							</div>
						{/each}

						{#if activityLogs.length === 0}
							<div class="py-8 text-center text-slate-500 dark:text-slate-400">No activity logs found</div>
						{/if}
					</div>

					<!-- Pagination -->
					{#if activityTotal > 50}
						<div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Showing {(activityPage - 1) * 50 + 1} to {Math.min(activityPage * 50, activityTotal)} of {activityTotal} logs
							</p>
							<div class="flex gap-2">
								<Button
									variant="secondary"
									size="sm"
									disabled={activityPage === 1}
									on:click={() => { activityPage--; loadActivity(); }}
								>
									Previous
								</Button>
								<Button
									variant="secondary"
									size="sm"
									disabled={activityPage * 50 >= activityTotal}
									on:click={() => { activityPage++; loadActivity(); }}
								>
									Next
								</Button>
							</div>
						</div>
					{/if}
				</Card>
			{/if}
		</div>
	{/if}

	<!-- SSL Tab -->
	{#if activeTab === 'ssl'}
		<div class="space-y-6">
			{#if loadingSSL}
				<div class="animate-pulse space-y-4">
					<div class="h-32 rounded-xl bg-slate-200"></div>
					<div class="h-64 rounded-xl bg-slate-200"></div>
				</div>
			{:else}
				<!-- Current Status -->
				<Card>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Current SSL Status</h3>
					<div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<div class="rounded-lg bg-slate-50 dark:bg-slate-700/40 p-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">Mode</p>
							<p class="mt-1 font-medium text-slate-900 dark:text-white">
								{sslStatus ? getSSLModeLabel(sslStatus.mode) : 'Unknown'}
							</p>
						</div>
						<div class="rounded-lg bg-slate-50 dark:bg-slate-700/40 p-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">Status</p>
							<div class="mt-1 flex items-center gap-2">
								{#if sslStatus?.enabled}
									{#if sslStatus.certificate_valid}
										<span class="inline-flex h-2 w-2 rounded-full bg-green-500"></span>
										<span class="font-medium text-green-700 dark:text-green-300">Active & Valid</span>
									{:else}
										<span class="inline-flex h-2 w-2 rounded-full bg-yellow-500"></span>
										<span class="font-medium text-yellow-700">Certificate Invalid</span>
									{/if}
								{:else}
									<span class="inline-flex h-2 w-2 rounded-full bg-slate-400"></span>
									<span class="font-medium text-slate-600 dark:text-slate-400">Disabled</span>
								{/if}
							</div>
						</div>
						<div class="rounded-lg bg-slate-50 dark:bg-slate-700/40 p-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">Domain</p>
							<p class="mt-1 font-medium text-slate-900 dark:text-white">
								{sslStatus?.domain || 'Not configured'}
							</p>
						</div>
						<div class="rounded-lg bg-slate-50 dark:bg-slate-700/40 p-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">Certificate Expiry</p>
							<p class="mt-1 font-medium text-slate-900 dark:text-white">
								{#if sslStatus?.certificate_expiry}
									{new Date(sslStatus.certificate_expiry).toLocaleDateString()}
									{#if sslStatus.days_until_expiry !== null}
										<span class="text-sm text-slate-500 dark:text-slate-400">
											({sslStatus.days_until_expiry} days)
										</span>
									{/if}
								{:else}
									N/A
								{/if}
							</p>
						</div>
					</div>

					{#if sslStatus?.last_error}
						<div class="mt-4 rounded-lg bg-red-50 dark:bg-red-900/20 p-4">
							<p class="text-sm font-medium text-red-800 dark:text-red-200">Last Error:</p>
							<p class="mt-1 text-sm text-red-700 dark:text-red-300">{sslStatus.last_error}</p>
						</div>
					{/if}

					{#if sslStatus?.enabled && sslStatus?.certificate_valid}
						<div class="mt-4 flex gap-2">
							<Button variant="secondary" on:click={handleTestCertificate}>
								Test Certificate
							</Button>
							{#if sslStatus.mode === 'letsencrypt'}
								<Button variant="secondary" on:click={handleRenewCertificate} loading={generatingCert}>
									Renew Certificate
								</Button>
							{/if}
						</div>
					{/if}
				</Card>

				<!-- Configure SSL -->
				<Card>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Configure SSL/HTTPS</h3>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Enable HTTPS to secure your connection and allow camera access on mobile devices.
					</p>

					<div class="mt-6 space-y-4">
						<div>
							<label for="ssl-mode" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">SSL Mode</label>
							<select
								id="ssl-mode"
								bind:value={sslFormData.mode}
								class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
							>
								<option value="disabled">Disabled (HTTP only)</option>
								<option value="self_signed">Self-Signed Certificate (for local/testing)</option>
								<option value="letsencrypt">Let's Encrypt (for production)</option>
							</select>
						</div>

						{#if sslFormData.mode === 'self_signed'}
							<div class="rounded-lg bg-amber-50 dark:bg-amber-900/20 p-4">
								<p class="text-sm text-amber-800 dark:text-amber-200">
									<strong>Note:</strong> Self-signed certificates will show a browser warning.
									Users will need to accept the certificate to proceed. This is suitable for
									local networks and testing.
								</p>
							</div>

							<div>
								<label for="ssl-domain" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Domain (optional)
								</label>
								<input
									id="ssl-domain"
									type="text"
									bind:value={sslFormData.domain}
									placeholder="e.g., storagehub.local or 192.168.1.100"
									class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
								/>
								<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Leave blank to use 'storagehub.local' as the certificate name
								</p>
							</div>
						{/if}

						{#if sslFormData.mode === 'letsencrypt'}
							<div class="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4">
								<p class="text-sm text-blue-800 dark:text-blue-200">
									<strong>Requirements:</strong> Your server must be accessible from the internet
									on port 80, and you need a valid domain name pointing to this server.
								</p>
							</div>

							<div>
								<label for="ssl-domain-le" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Domain <span class="text-red-500">*</span>
								</label>
								<input
									id="ssl-domain-le"
									type="text"
									bind:value={sslFormData.domain}
									placeholder="e.g., storagehub.example.com"
									required
									class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
								/>
							</div>

							<div>
								<label for="ssl-email" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Email <span class="text-red-500">*</span>
								</label>
								<input
									id="ssl-email"
									type="email"
									bind:value={sslFormData.email}
									placeholder="admin@example.com"
									required
									class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
								/>
								<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Used for certificate expiry notifications from Let's Encrypt
								</p>
							</div>
						{/if}

						<div class="flex gap-2 pt-4">
							<Button on:click={handleGenerateCertificate} loading={generatingCert}>
								{#if sslFormData.mode === 'disabled'}
									Disable HTTPS
								{:else if sslFormData.mode === 'self_signed'}
									Generate Self-Signed Certificate
								{:else}
									Request Let's Encrypt Certificate
								{/if}
							</Button>
						</div>
					</div>
				</Card>

				<!-- Help -->
				<Card>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">About HTTPS</h3>
					<div class="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-400">
						<p>
							<strong>Why enable HTTPS?</strong> Modern browsers require HTTPS to access
							device features like the camera. Without HTTPS, QR code scanning won't work
							on mobile devices.
						</p>
						<p>
							<strong>Self-Signed vs Let's Encrypt:</strong> Self-signed certificates are
							quick to set up and work for local networks, but browsers will show a warning.
							Let's Encrypt provides free, trusted certificates but requires a public domain.
						</p>
						<p>
							<strong>After enabling HTTPS:</strong> Access your site using https:// instead
							of http://. If using a self-signed certificate, you'll need to accept the
							browser warning once.
						</p>
					</div>
				</Card>
			{/if}
		</div>
	{/if}

	<!-- AI Settings Tab -->
	{#if activeTab === 'ai'}
		<div class="space-y-6">
			{#if loadingAI}
				<div class="flex justify-center py-12">
					<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
				</div>
			{:else}
				<!-- Languages -->
				{#if languageSettings}
					<Card>
						<div class="flex items-center justify-between">
							<div>
								<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Languages</h3>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									ISO codes the AI generates names and descriptions in. Adding a language only
									affects items processed from now on — existing items keep their original
									translations until re-processed.
								</p>
							</div>
						</div>

						<div class="mt-4 flex flex-wrap gap-2">
							{#each languageSettings.supported_languages as code}
								<div class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-sm dark:bg-slate-700">
									<span class="font-mono uppercase text-slate-700 dark:text-slate-200">{code}</span>
									{#if code === languageSettings.default_language}
										<span class="rounded bg-primary-100 px-1.5 py-0.5 text-xs font-medium text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">default</span>
									{:else}
										<button
											type="button"
											class="text-xs text-primary-600 hover:underline dark:text-primary-400"
											on:click={() => setDefaultLanguage(code)}
											disabled={savingLanguages}
										>
											make default
										</button>
									{/if}
									{#if languageSettings.supported_languages.length > 1}
										<button
											type="button"
											class="text-slate-400 hover:text-red-600 dark:hover:text-red-400"
											on:click={() => removeLanguage(code)}
											disabled={savingLanguages}
											title="Remove"
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
										</button>
									{/if}
								</div>
							{/each}
						</div>

						<form
							class="mt-4 flex gap-2"
							on:submit|preventDefault={addLanguage}
						>
							<Input
								bind:value={newLanguageInput}
								placeholder="ISO code (e.g. de, sv, fr)"
								disabled={savingLanguages}
							/>
							<Button type="submit" loading={savingLanguages}>Add language</Button>
						</form>
						<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
							Note: a UI translation file must also exist in the source for the language to be
							selectable as a user preference. AI content will still be generated either way.
						</p>
					</Card>
				{/if}

				<!-- OpenAI Classification Settings -->
				<Card>
					<div class="flex items-center justify-between">
						<div>
							<h3 class="text-lg font-semibold text-slate-900 dark:text-white">OpenAI Classification</h3>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								AI-powered item classification and description generation
							</p>
						</div>
						{#if openaiSettings?.api_key_set}
							<span class="flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700 dark:text-green-300">
								<span class="h-1.5 w-1.5 rounded-full bg-green-500"></span>
								API Key Set
							</span>
						{:else}
							<span class="flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700 dark:text-amber-300">
								<span class="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
								No API Key
							</span>
						{/if}
					</div>

					{#if openaiSettings}
						<div class="mt-6 space-y-6">
							<!-- Vision Classification -->
							<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
								<div class="flex items-center justify-between">
									<div>
										<h4 class="font-medium text-slate-900 dark:text-white">Vision Classification</h4>
										<p class="text-xs text-slate-500 dark:text-slate-400">Used for analyzing item photos</p>
									</div>
									<label class="relative inline-flex cursor-pointer items-center">
										<input type="checkbox" bind:checked={openaiFormData.vision_enabled} class="peer sr-only" />
										<div class="peer h-6 w-11 rounded-full bg-slate-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-slate-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300"></div>
									</label>
								</div>

								<div class="mt-4 grid gap-4 sm:grid-cols-2">
									<div>
										<label for="vision-model" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
											Model
										</label>
										<select
											id="vision-model"
											bind:value={openaiFormData.vision_model}
											class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
										>
											{#each openaiSettings.vision_models as model}
												<option value={model.id}>{model.name} - {model.description}</option>
											{/each}
										</select>
									</div>

									<div>
										<label for="vision-tokens" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
											Max Tokens: {openaiFormData.vision_max_tokens}
										</label>
										<input
											id="vision-tokens"
											type="range"
											min="200"
											max="2000"
											step="100"
											bind:value={openaiFormData.vision_max_tokens}
											class="w-full"
										/>
									</div>
								</div>

								<div class="mt-4">
									<label for="vision-temp" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
										Temperature: {openaiFormData.vision_temperature.toFixed(2)}
									</label>
									<input
										id="vision-temp"
										type="range"
										min="0"
										max="1"
										step="0.05"
										bind:value={openaiFormData.vision_temperature}
										class="w-full"
									/>
									<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
										Lower = more consistent, Higher = more creative
									</p>
								</div>

								<!-- Cost estimate (reactive — recomputes on any form change) -->
								{#if visionLiveCost}
									<div class="mt-4 rounded-lg bg-slate-50 dark:bg-slate-700/40 p-3">
										<p class="text-sm text-slate-600 dark:text-slate-400">
											<span class="font-medium">Max cost per image:</span>
											${visionLiveCost.cost.toFixed(5)}
										</p>
										<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
											~{visionLiveCost.inputTokens} input + up to {visionLiveCost.outputTokens} output tokens
										</p>
									</div>
								{/if}
							</div>

							<!-- Summary Generation -->
							<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
								<div class="flex items-center justify-between">
									<div>
										<h4 class="font-medium text-slate-900 dark:text-white">Summary Generation</h4>
										<p class="text-xs text-slate-500 dark:text-slate-400">Used for container label summaries</p>
									</div>
									<label class="relative inline-flex cursor-pointer items-center">
										<input type="checkbox" bind:checked={openaiFormData.summary_enabled} class="peer sr-only" />
										<div class="peer h-6 w-11 rounded-full bg-slate-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-slate-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300"></div>
									</label>
								</div>

								<div class="mt-4 grid gap-4 sm:grid-cols-2">
									<div>
										<label for="summary-model" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
											Model
										</label>
										<select
											id="summary-model"
											bind:value={openaiFormData.summary_model}
											class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
										>
											{#each openaiSettings.text_models as model}
												<option value={model.id}>{model.name} - {model.description}</option>
											{/each}
										</select>
									</div>

									<div>
										<label for="summary-tokens" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
											Max Tokens: {openaiFormData.summary_max_tokens}
										</label>
										<input
											id="summary-tokens"
											type="range"
											min="50"
											max="500"
											step="25"
											bind:value={openaiFormData.summary_max_tokens}
											class="w-full"
										/>
									</div>
								</div>

								<div class="mt-4">
									<label for="summary-temp" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
										Temperature: {openaiFormData.summary_temperature.toFixed(2)}
									</label>
									<input
										id="summary-temp"
										type="range"
										min="0"
										max="1"
										step="0.05"
										bind:value={openaiFormData.summary_temperature}
										class="w-full"
									/>
									<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
										Lower = more consistent, Higher = more creative
									</p>
								</div>

								<!-- Cost estimate (reactive — recomputes on any form change) -->
								{#if summaryLiveCost}
									<div class="mt-4 rounded-lg bg-slate-50 dark:bg-slate-700/40 p-3">
										<p class="text-sm text-slate-600 dark:text-slate-400">
											<span class="font-medium">Max cost per summary:</span>
											${summaryLiveCost.cost.toFixed(6)}
										</p>
										<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
											~{summaryLiveCost.inputTokens} input + up to {summaryLiveCost.outputTokens} output tokens
										</p>
									</div>
								{/if}
							</div>

							<!-- AI Owner Suggestion -->
							<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
								<div class="flex items-center justify-between">
									<div>
										<h4 class="font-medium text-slate-900 dark:text-white">AI Owner Suggestion</h4>
										<p class="text-xs text-slate-500 dark:text-slate-400">
											When classifying an item, also pick the most likely owner from
											non-admin users using their birthdate + gender. Surfaced as a
											banner on the item page; never auto-assigns.
										</p>
									</div>
									<label class="relative inline-flex cursor-pointer items-center">
										<input
											type="checkbox"
											bind:checked={openaiFormData.owner_suggestion_enabled}
											class="peer sr-only"
										/>
										<div class="peer h-6 w-11 rounded-full bg-slate-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-slate-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-300"></div>
									</label>
								</div>
							</div>

							<!-- Size Age Backfill -->
							<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
								<div class="flex items-start justify-between gap-4">
									<div>
										<h4 class="font-medium text-slate-900 dark:text-white">Recompute Size Age Ranges</h4>
										<p class="text-xs text-slate-500 dark:text-slate-400">
											Infers an age range (in months) from the size string of every
											existing item that doesn't have one yet. Drives the
											<a href="/outgrown" class="underline">Outgrown</a> page. Cheap text-only
											AI call per item; safe to re-run.
										</p>
									</div>
									<Button
										variant="secondary"
										size="sm"
										loading={recomputingSizeAges}
										on:click={handleRecomputeSizeAges}
									>
										Recompute
									</Button>
								</div>
							</div>

							<div class="flex justify-end pt-2">
								<Button on:click={handleSaveOpenAISettings} loading={savingOpenAI}>
									Save OpenAI Settings
								</Button>
							</div>
						</div>
					{:else}
						<div class="mt-4 text-sm text-slate-500 dark:text-slate-400">
							Loading OpenAI settings...
						</div>
					{/if}
				</Card>

				<!-- OpenAI Help -->
				<Card>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">About OpenAI Classification</h3>
					<div class="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-400">
						<p>
							<strong>Vision Classification:</strong> When you add a new item, the AI analyzes the photo
							to automatically generate a name, description, tags, and detect size/season information.
						</p>
						<p>
							<strong>Summary Generation:</strong> Creates helpful summaries for container labels,
							describing what's inside in 2-4 sentences.
						</p>
						<p>
							<strong>Model Selection:</strong> GPT-4o provides the best quality but costs more.
							GPT-4o-mini is a good balance of quality and cost for most uses.
						</p>
						<p>
							<strong>Cost Estimates:</strong> Shown costs are approximate. Actual costs depend on
							image complexity and response length. Check <a href="https://openai.com/api/pricing/" target="_blank" rel="noopener" class="text-primary-600 dark:text-primary-400 underline">OpenAI pricing</a> for current rates.
						</p>
					</div>
				</Card>
			{/if}
		</div>
	{/if}

	<!-- Backups Tab -->
	{#if activeTab === 'backups'}
		<div class="space-y-6">
			<!-- Quick Actions -->
			<Card>
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Create Backup</h3>
				<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
					Create a backup of your database. Backups include all locations, containers, items, and tags.
				</p>

				<div class="mt-4 space-y-4">
					<div class="flex flex-wrap gap-4">
						<label class="flex items-center gap-2">
							<input
								type="checkbox"
								bind:checked={backupOptions.include_images}
								class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400"
							/>
							<span class="text-sm text-slate-700 dark:text-slate-300">Include images</span>
						</label>
					</div>

					<div class="flex flex-wrap gap-3">
						<Button on:click={handleQuickDownload} variant="primary">
							<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
							</svg>
							Download Backup Now
						</Button>
						<Button on:click={handleCreateBackup} variant="secondary" loading={creatingBackup}>
							<svg class="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
							</svg>
							Save to History
						</Button>
					</div>
				</div>
			</Card>

			<!-- Restore from File -->
			<Card>
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Restore from File</h3>
				<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
					Upload a backup file to restore data. New items will be added; existing items won't be overwritten.
				</p>

				<div class="mt-4">
					<label class="flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 p-6 hover:border-primary-400 hover:bg-slate-50 dark:hover:bg-slate-700/50">
						<svg class="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
						</svg>
						<span class="text-sm text-slate-600 dark:text-slate-400">Click to select a backup file (.zip)</span>
						<input
							type="file"
							accept=".zip"
							class="hidden"
							on:change={handleFileUpload}
							disabled={restoringBackup}
						/>
					</label>
				</div>
			</Card>

			<!-- Backup History -->
			<Card>
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Backup History</h3>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Previous backups stored on the server</p>
					</div>
					<button
						on:click={loadBackups}
						class="rounded-lg p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
						title="Refresh"
					>
						<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
					</button>
				</div>

				{#if loadingBackups}
					<div class="mt-4 animate-pulse space-y-2">
						{#each [1, 2, 3] as _}
							<div class="h-16 rounded-lg bg-slate-200"></div>
						{/each}
					</div>
				{:else if backups.length === 0}
					<div class="mt-4 py-8 text-center text-slate-500 dark:text-slate-400">
						No backups found. Create your first backup above.
					</div>
				{:else}
					<div class="mt-4 divide-y divide-slate-100">
						{#each backups as b}
							<div class="flex items-center justify-between py-3">
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2">
										<p class="truncate font-medium text-slate-900 dark:text-white">{b.filename || 'Unknown'}</p>
										<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {backup.getStatusColor(b.status)}">
											{b.status}
										</span>
									</div>
									<div class="mt-1 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
										<span>{backup.formatBytes(b.size_bytes)}</span>
										{#if b.completed_at}
											<span>{formatDateTime(b.completed_at)}</span>
										{/if}
										{#if b.statistics}
											<span>
												{b.statistics.items_count || 0} items
											</span>
										{/if}
									</div>
								</div>
								<div class="flex items-center gap-1 ml-4">
									{#if b.status === 'completed'}
										<button
											class="rounded p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
											title="Download"
											on:click={() => handleDownloadBackup(b)}
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
											</svg>
										</button>
										{#if googleDriveConnected}
											<button
												class="rounded p-1.5 text-slate-400 hover:bg-blue-50 hover:text-blue-600"
												title="Upload to Google Drive"
												on:click={() => handleUploadToGoogleDrive(b)}
												disabled={uploadingToGoogleDrive}
											>
												<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
												</svg>
											</button>
										{/if}
										{#if dropboxConnected}
											<button
												class="rounded p-1.5 text-slate-400 hover:bg-indigo-50 hover:text-indigo-600"
												title="Upload to Dropbox"
												on:click={() => handleUploadToDropbox(b)}
												disabled={uploadingToDropbox}
											>
												<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
												</svg>
											</button>
										{/if}
										<button
											class="rounded p-1.5 text-slate-400 hover:bg-green-50 hover:text-green-600"
											title="Restore"
											on:click={() => handleRestoreFromHistory(b)}
											disabled={restoringBackup}
										>
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
											</svg>
										</button>
									{/if}
									<button
										class="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
										title="Delete"
										on:click={() => handleDeleteBackup(b)}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								</div>
							</div>
						{/each}
					</div>

					<!-- Pagination -->
					{#if backupsTotal > 20}
						<div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Showing {(backupsPage - 1) * 20 + 1} to {Math.min(backupsPage * 20, backupsTotal)} of {backupsTotal}
							</p>
							<div class="flex gap-2">
								<Button
									variant="secondary"
									size="sm"
									disabled={backupsPage === 1}
									on:click={() => { backupsPage--; loadBackups(); }}
								>
									Previous
								</Button>
								<Button
									variant="secondary"
									size="sm"
									disabled={backupsPage * 20 >= backupsTotal}
									on:click={() => { backupsPage++; loadBackups(); }}
								>
									Next
								</Button>
							</div>
						</div>
					{/if}
				{/if}
			</Card>

			<!-- Scheduled Backups -->
			<Card>
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Scheduled Backups</h3>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Configure automatic backups to run on a schedule.
						</p>
					</div>
				</div>

				{#if loadingSchedules}
					<div class="mt-4 animate-pulse space-y-2">
						<div class="h-12 rounded bg-slate-200"></div>
					</div>
				{:else if schedules.length === 0}
					<div class="mt-4 rounded-lg border-2 border-dashed border-slate-200 dark:border-slate-700 p-6 text-center">
						<svg class="mx-auto h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">No scheduled backups configured.</p>
						<p class="mt-1 text-xs text-slate-400">
							Create a backup configuration first, then add schedules via the API.
						</p>
					</div>
				{:else}
					<div class="mt-4 divide-y divide-slate-100 rounded-lg border border-slate-200 dark:border-slate-700">
						{#each schedules as schedule}
							<div class="flex items-center justify-between p-4">
								<div class="min-w-0 flex-1">
									<div class="flex items-center gap-2">
										<p class="font-medium text-slate-900 dark:text-white">{schedule.name}</p>
										<span class="rounded-full px-2 py-0.5 text-xs font-medium {schedule.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'}">
											{schedule.is_active ? 'Active' : 'Paused'}
										</span>
									</div>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										{backup.formatScheduleDescription(schedule)}
									</p>
									{#if schedule.next_run_at}
										<p class="mt-0.5 text-xs text-slate-400">
											Next run: {formatDateTime(schedule.next_run_at)}
										</p>
									{/if}
								</div>
								<div class="flex items-center gap-1 ml-4">
									<button
										class="rounded p-1.5 text-slate-400 hover:bg-blue-50 hover:text-blue-600"
										title="Run Now"
										on:click={() => handleRunScheduleNow(schedule)}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
										</svg>
									</button>
									<button
										class="rounded p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
										title={schedule.is_active ? 'Pause' : 'Activate'}
										on:click={() => handleToggleSchedule(schedule)}
									>
										{#if schedule.is_active}
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
											</svg>
										{:else}
											<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
											</svg>
										{/if}
									</button>
									<button
										class="rounded p-1.5 text-slate-400 hover:bg-amber-50 hover:text-amber-600"
										title="Edit"
										on:click={() => openEditScheduleModal(schedule)}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
										</svg>
									</button>
									<button
										class="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
										title="Delete"
										on:click={() => handleDeleteSchedule(schedule)}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</Card>

			<!-- Google Drive Integration -->
			{#if providerStatus?.google_drive_available}
				<Card>
					<div class="flex items-start justify-between">
						<div>
							<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Google Drive Integration</h3>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								Store backups in Google Drive for offsite protection.
							</p>
						</div>
						<span class="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 dark:text-amber-200">
							Workspace Only
						</span>
					</div>

					<!-- Workspace Requirement Notice -->
					<div class="mt-3 rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-3">
						<p class="text-xs font-medium text-amber-800 dark:text-amber-200">Requires Google Workspace</p>
						<p class="mt-1 text-xs text-amber-700 dark:text-amber-300">
							Google Drive with service accounts requires a <strong>Google Workspace</strong> account (Business, Education, etc.) with <strong>Shared Drives</strong>.
							Personal Gmail accounts cannot use this feature due to storage quota limitations.
							<a href="/admin/google-drive-setup" class="font-medium underline">Learn more</a>
						</p>
					</div>

					{#if googleDriveConnected}
						<!-- Connected State -->
						<div class="mt-4">
							<div class="flex items-center gap-3 rounded-lg {googleDriveWarning ? 'bg-amber-50 dark:bg-amber-900/20' : 'bg-green-50'} p-4">
								{#if googleDriveWarning}
									<svg class="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
									</svg>
								{:else}
									<svg class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
								{/if}
								<div class="flex-1">
									<p class="text-sm font-medium {googleDriveWarning ? 'text-amber-800 dark:text-amber-200' : 'text-green-800'}">
										{googleDriveWarning ? 'Connected - Action Required' : 'Connected to Google Drive'}
									</p>
									{#if googleDriveEmail}
										<p class="text-xs {googleDriveWarning ? 'text-amber-600' : 'text-green-600 dark:text-green-400'}">{googleDriveEmail}</p>
									{/if}
								</div>
								<Button variant="secondary" size="sm" on:click={disconnectGoogleDrive}>
									Disconnect
								</Button>
							</div>

							{#if googleDriveWarning}
								<div class="mt-3 rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 p-4">
									<p class="text-sm font-medium text-red-800 dark:text-red-200">Shared Drive Required</p>
									<p class="mt-1 text-sm text-red-700 dark:text-red-300">
										Service accounts cannot upload to regular Google Drive due to storage quota limitations.
										You need a <strong>Google Workspace account</strong> with a <strong>Shared Drive</strong> (Team Drive).
									</p>
									<div class="mt-3 rounded bg-red-100 p-3 text-xs text-red-800 dark:text-red-200">
										<p class="font-medium">Why won't regular shared folders work?</p>
										<p class="mt-1">When a service account uploads a file, it owns that file. Storage quota is based on ownership, not file location. Service accounts have zero storage quota, so uploads always fail - even to shared folders.</p>
									</div>
									<div class="mt-3 space-y-2 text-sm text-red-700 dark:text-red-300">
										<p class="font-medium">Options:</p>
										<ol class="ml-4 list-decimal space-y-1">
											<li>Use a Google Workspace account and create a Shared Drive</li>
											<li>Add the service account as a member of the Shared Drive</li>
											<li>Or use a different backup method (local storage)</li>
										</ol>
									</div>
									<a
										href="/admin/google-drive-setup"
										class="mt-3 inline-flex items-center gap-1 text-sm font-medium text-red-700 dark:text-red-300 hover:text-red-900 hover:underline"
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
										</svg>
										View setup guide
									</a>
								</div>
							{:else if googleDriveSharedDrives.length > 0}
								<div class="mt-3 rounded-lg border border-green-200 bg-green-50 dark:bg-green-900/20 p-3">
									<p class="text-sm font-medium text-green-800 dark:text-green-200">Available Shared Drives:</p>
									<ul class="mt-1 space-y-1">
										{#each googleDriveSharedDrives as drive}
											<li class="text-sm text-green-700 dark:text-green-300">• {drive.name}</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- Remote Backups -->
							<div class="mt-4">
								<div class="flex items-center justify-between">
									<h4 class="text-sm font-medium text-slate-700 dark:text-slate-300">Backups in Google Drive</h4>
									<button
										on:click={loadRemoteBackups}
										class="rounded p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
										title="Refresh"
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
										</svg>
									</button>
								</div>

								{#if loadingRemoteBackups}
									<div class="mt-2 animate-pulse space-y-2">
										{#each [1, 2] as _}
											<div class="h-12 rounded bg-slate-200"></div>
										{/each}
									</div>
								{:else if remoteBackups.length === 0}
									<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">No backups in Google Drive yet.</p>
								{:else}
									<div class="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200 dark:border-slate-700">
										{#each remoteBackups as rb}
											<div class="flex items-center justify-between p-3">
												<div class="min-w-0 flex-1">
													<p class="truncate text-sm font-medium text-slate-900 dark:text-white">{rb.filename}</p>
													<p class="text-xs text-slate-500 dark:text-slate-400">
														{backup.formatBytes(rb.size_bytes)} - {formatDateTime(rb.created_at)}
													</p>
												</div>
												<button
													class="ml-2 rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
													title="Delete from Google Drive"
													on:click={() => handleDeleteFromGoogleDrive(rb.remote_id, rb.filename)}
												>
													<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
												</button>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					{:else}
						<!-- Setup State -->
						<div class="mt-4 space-y-4">
							<div class="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4">
								<p class="text-sm text-blue-800 dark:text-blue-200">
									<strong>Setup:</strong> Create a Service Account in Google Cloud Console,
									enable the Drive API, and download the JSON key file. Paste the contents below.
								</p>
								<a
									href="/admin/google-drive-setup"
									class="mt-2 inline-flex items-center gap-1 text-sm font-medium text-blue-700 dark:text-blue-300 hover:text-blue-900 hover:underline"
								>
									<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
									View step-by-step setup guide
								</a>
							</div>

							<div>
								<label for="gdrive-creds" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Service Account JSON
								</label>
								<textarea
									id="gdrive-creds"
									bind:value={googleDriveCredentials}
									rows="4"
									placeholder="Paste service account JSON here..."
									class="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 font-mono text-xs focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
								></textarea>
							</div>

							<Button on:click={handleTestGoogleDrive} loading={testingGoogleDrive}>
								Connect to Google Drive
							</Button>
						</div>
					{/if}
				</Card>
			{/if}

			<!-- Dropbox Integration -->
			{#if providerStatus?.dropbox_available}
				<Card>
					<div class="flex items-start justify-between">
						<div>
							<h3 class="text-lg font-semibold text-slate-900 dark:text-white">Dropbox Integration</h3>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								Store backups in Dropbox for offsite protection.
							</p>
						</div>
						<span class="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800 dark:text-green-200">
							Personal & Business
						</span>
					</div>

					<!-- Personal Account Notice -->
					<div class="mt-3 rounded-lg border border-green-200 bg-green-50 dark:bg-green-900/20 p-3">
						<p class="text-xs font-medium text-green-800 dark:text-green-200">Works with personal accounts</p>
						<p class="mt-1 text-xs text-green-700 dark:text-green-300">
							Dropbox works with both <strong>personal</strong> and <strong>business</strong> accounts.
							Simply generate an access token from the Dropbox App Console.
						</p>
					</div>

					{#if dropboxConnected}
						<!-- Connected State -->
						<div class="mt-4">
							<div class="flex items-center gap-3 rounded-lg bg-green-50 dark:bg-green-900/20 p-4">
								<svg class="h-5 w-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								<div class="flex-1">
									<p class="text-sm font-medium text-green-800 dark:text-green-200">Connected to Dropbox</p>
									{#if dropboxAccountName}
										<p class="text-xs text-green-600 dark:text-green-400">{dropboxAccountName} ({dropboxEmail})</p>
									{/if}
								</div>
								<Button variant="secondary" size="sm" on:click={disconnectDropbox}>
									Disconnect
								</Button>
							</div>

							<!-- Dropbox Backups -->
							<div class="mt-4">
								<div class="flex items-center justify-between">
									<h4 class="text-sm font-medium text-slate-700 dark:text-slate-300">Backups in Dropbox</h4>
									<button
										on:click={loadDropboxBackups}
										class="rounded p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-600"
										title="Refresh"
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
										</svg>
									</button>
								</div>

								{#if loadingDropboxBackups}
									<div class="mt-2 animate-pulse space-y-2">
										{#each [1, 2] as _}
											<div class="h-12 rounded bg-slate-200"></div>
										{/each}
									</div>
								{:else if dropboxBackups.length === 0}
									<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">No backups in Dropbox yet.</p>
								{:else}
									<div class="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200 dark:border-slate-700">
										{#each dropboxBackups as rb}
											<div class="flex items-center justify-between p-3">
												<div class="min-w-0 flex-1">
													<p class="truncate text-sm font-medium text-slate-900 dark:text-white">{rb.filename}</p>
													<p class="text-xs text-slate-500 dark:text-slate-400">
														{backup.formatBytes(rb.size_bytes)} •
														{new Date(rb.created_at).toLocaleDateString()}
													</p>
												</div>
												<button
													class="ml-2 rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
													title="Delete from Dropbox"
													on:click={() => handleDeleteFromDropbox(rb.remote_id)}
												>
													<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
												</button>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						</div>
					{:else}
						<!-- Setup State -->
						<div class="mt-4 space-y-4">
							<div class="rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4">
								<p class="text-sm text-blue-800 dark:text-blue-200">
									<strong>Setup:</strong> Create a Dropbox App at <a href="https://www.dropbox.com/developers/apps" target="_blank" rel="noopener noreferrer" class="underline">dropbox.com/developers/apps</a>,
									generate an access token, and paste it below.
								</p>
								<ol class="mt-2 ml-4 list-decimal text-xs text-blue-700 dark:text-blue-300 space-y-1">
									<li>Go to <a href="https://www.dropbox.com/developers/apps" target="_blank" rel="noopener noreferrer" class="underline">Dropbox App Console</a></li>
									<li>Click "Create app" → Choose "Scoped access" → "Full Dropbox"</li>
									<li>Name your app (e.g., "StorageHub Backups")</li>
									<li>In the app settings, go to "Permissions" tab and enable files.content.write and files.content.read</li>
									<li>Go to "Settings" tab and click "Generate access token"</li>
								</ol>
							</div>

							<div>
								<label for="dropbox-token" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Access Token
								</label>
								<input
									id="dropbox-token"
									type="password"
									bind:value={dropboxAccessToken}
									placeholder="Enter your Dropbox access token"
									class="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 font-mono text-xs focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
								/>
							</div>

							<Button on:click={handleTestDropbox} loading={testingDropbox}>
								Connect to Dropbox
							</Button>
						</div>
					{/if}
				</Card>
			{/if}

			<!-- Help -->
			<Card>
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white">About Backups</h3>
				<div class="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-400">
					<p>
						<strong>What's included?</strong> Backups contain all your locations, containers,
						items, tags, and optionally images. User accounts are not included in backups.
					</p>
					<p>
						<strong>Restore behavior:</strong> Restoring a backup adds new data without overwriting
						existing records. Items with matching QR codes or names are skipped.
					</p>
					<p>
						<strong>Storage:</strong> Backups are saved as ZIP files. Include images for a complete
						backup, or exclude them for a smaller file size.
					</p>
					{#if providerStatus?.google_drive_available}
						<p>
							<strong>Google Drive:</strong> Requires a Google Workspace account with Shared Drives.
							Personal Gmail accounts cannot use this feature.
						</p>
					{/if}
					{#if providerStatus?.dropbox_available}
						<p>
							<strong>Dropbox:</strong> Works with both personal and business accounts.
							Simply generate an access token to connect.
						</p>
					{/if}
				</div>
			</Card>
		</div>
	{/if}
</div>

<!-- User Modal -->
{#if showUserModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-800">
			<h2 class="text-xl font-bold text-slate-900 dark:text-white">
				{editingUser ? 'Edit User' : 'Create User'}
			</h2>

			<form on:submit|preventDefault={handleSaveUser} class="mt-4 space-y-4">
				<div>
					<label for="user-name" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Name</label>
					<input
						id="user-name"
						type="text"
						bind:value={userFormData.name}
						required
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
					/>
				</div>

				<div>
					<label for="user-email" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Email (optional)</label>
					<input
						id="user-email"
						type="email"
						bind:value={userFormData.email}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
					/>
				</div>

				<div>
					<label for="user-role" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Role</label>
					<select
						id="user-role"
						bind:value={userFormData.role}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
					>
						<option value="user">User</option>
						<option value="admin">Admin</option>
					</select>
				</div>

				<div>
					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							bind:checked={userFormData.requires_password}
							disabled={userFormData.is_profile}
							class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400 disabled:opacity-50"
						/>
						<span class="text-sm text-slate-700 dark:text-slate-300">Require password to login</span>
					</label>
				</div>

				{#if userFormData.requires_password && !userFormData.is_profile}
					<div>
						<label for="user-password" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
							{editingUser ? 'New Password (leave blank to keep current)' : 'Password'}
						</label>
						<input
							id="user-password"
							type="password"
							bind:value={userFormData.password}
							required={!editingUser && userFormData.requires_password}
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
						/>
					</div>
				{/if}

				{#if userFormData.role !== 'admin'}
					<div class="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-700/40">
						<label class="flex items-start gap-2">
							<input
								type="checkbox"
								bind:checked={userFormData.is_profile}
								on:change={() => {
									if (userFormData.is_profile) userFormData.requires_password = false;
								}}
								class="mt-0.5 h-4 w-4 rounded border-slate-300 text-primary-600 dark:text-primary-400 dark:border-slate-600"
							/>
							<span class="text-sm text-slate-700 dark:text-slate-300">
								<span class="font-medium">Profile (no login)</span>
								<span class="block text-xs text-slate-500 dark:text-slate-400">
									For household members who own items but never sign in (e.g. small kids).
									Hidden from the login screen.
								</span>
							</span>
						</label>
					</div>

					<div class="grid grid-cols-2 gap-3">
						<div>
							<label for="user-birthdate" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Birthdate</label>
							<input
								id="user-birthdate"
								type="date"
								bind:value={userFormData.birthdate}
								class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
							/>
						</div>
						<div>
							<label for="user-gender" class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">Gender</label>
							<select
								id="user-gender"
								bind:value={userFormData.gender}
								class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder-slate-500"
							>
								<option value="">—</option>
								<option value="male">Male</option>
								<option value="female">Female</option>
								<option value="other">Other</option>
							</select>
						</div>
					</div>
				{/if}

				{#if editingUser}
					<div>
						<label class="flex items-center gap-2">
							<input
								type="checkbox"
								bind:checked={userFormData.is_active}
								class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-primary-600 dark:text-primary-400"
							/>
							<span class="text-sm text-slate-700 dark:text-slate-300">Active</span>
						</label>
					</div>
				{/if}
			</form>

			<div class="mt-6 flex justify-end gap-3">
				<Button variant="secondary" on:click={() => showUserModal = false}>
					Cancel
				</Button>
				<Button loading={savingUser} on:click={handleSaveUser}>
					{editingUser ? 'Save Changes' : 'Create User'}
				</Button>
			</div>
		</div>
	</div>
{/if}

<!-- Restore Preview Modal -->
{#if showRestoreModal && restorePreview}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-800">
			<h2 class="text-xl font-bold text-slate-900 dark:text-white">Restore Backup</h2>

			<div class="mt-4 space-y-4">
				<div class="rounded-lg bg-slate-50 p-4 dark:bg-slate-700/40">
					<p class="text-sm font-medium text-slate-700 dark:text-slate-200">Backup Details</p>
					<div class="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-300">
						<p>Version: {restorePreview.version || 'Unknown'}</p>
						{#if restorePreview.created_at}
							<p>Created: {formatDateTime(restorePreview.created_at)}</p>
						{/if}
						{#if restorePreview.statistics}
							<p>Locations: {restorePreview.statistics.locations_count || 0}</p>
							<p>Containers: {restorePreview.statistics.containers_count || 0}</p>
							<p>Items: {restorePreview.statistics.items_count || 0}</p>
							<p>Tags: {restorePreview.statistics.tags_count || 0}</p>
							{#if restorePreview.statistics.images_count}
								<p>Images: {restorePreview.statistics.images_count}</p>
							{/if}
						{/if}
					</div>
				</div>

				<div class="rounded-lg bg-amber-50 p-4 dark:bg-amber-900/20">
					<p class="text-sm text-amber-800 dark:text-amber-200">
						<strong>Note:</strong> Restore will add new items. Existing records with matching
						QR codes or names will be skipped.
					</p>
				</div>

				<div>
					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							bind:checked={restoreOptions.restore_images}
							class="h-4 w-4 rounded border-slate-300 text-primary-600 dark:text-primary-400 dark:border-slate-600"
						/>
						<span class="text-sm text-slate-700 dark:text-slate-300">Restore images (if included in backup)</span>
					</label>
				</div>
			</div>

			<div class="mt-6 flex justify-end gap-3">
				<Button variant="secondary" on:click={cancelRestore}>
					Cancel
				</Button>
				<Button loading={restoringBackup} on:click={handleExecuteRestore}>
					Restore
				</Button>
			</div>
		</div>
	</div>
{/if}
