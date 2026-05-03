<script lang="ts">
	import { goto } from '$app/navigation';
</script>

<svelte:head>
	<title>Google Drive Setup Guide - StorageHub</title>
</svelte:head>

<div class="mx-auto max-w-3xl space-y-8 p-6">
	<!-- Header -->
	<div>
		<button
			on:click={() => goto('/admin')}
			class="mb-4 flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700"
		>
			<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back to Admin
		</button>
		<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Google Drive Setup Guide</h1>
		<p class="mt-2 text-slate-600 dark:text-slate-400">
			Follow these steps to connect StorageHub to Google Drive for offsite backup storage.
		</p>
	</div>

	<!-- Important Notice -->
	<section class="rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 p-4">
		<h2 class="flex items-center gap-2 font-semibold text-red-900">
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
			</svg>
			Important: Google Workspace Required
		</h2>
		<div class="mt-2 space-y-2 text-sm text-red-800 dark:text-red-200">
			<p>
				<strong>Service accounts cannot use personal Gmail accounts for backup storage.</strong>
			</p>
			<p>
				This is because service accounts have <strong>zero storage quota</strong>. When they upload files,
				even to shared folders, the files are owned by the service account and count against its (non-existent) quota.
			</p>
			<p class="font-medium">
				You need a <strong>Google Workspace</strong> account with access to <strong>Shared Drives</strong> (Team Drives).
			</p>
		</div>
	</section>

	<!-- Prerequisites -->
	<section class="rounded-lg border border-blue-200 bg-blue-50 dark:bg-blue-900/20 p-4">
		<h2 class="flex items-center gap-2 font-semibold text-blue-900">
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			Prerequisites
		</h2>
		<ul class="mt-2 space-y-1 text-sm text-blue-800 dark:text-blue-200">
			<li>A <strong>Google Workspace</strong> account (Business, Enterprise, Education, or Nonprofits)</li>
			<li>Access to Google Cloud Console</li>
			<li>Admin access to create a Shared Drive (or an existing one you can use)</li>
		</ul>
	</section>

	<!-- Step 1 -->
	<section class="space-y-4">
		<h2 class="flex items-center gap-3 text-lg font-semibold text-slate-900 dark:text-white">
			<span class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm text-white">1</span>
			Create a Google Cloud Project
		</h2>
		<div class="ml-11 space-y-3 text-slate-600 dark:text-slate-400">
			<ol class="list-decimal space-y-2 pl-4">
				<li>
					Go to <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer" class="text-primary-600 dark:text-primary-400 hover:underline">console.cloud.google.com</a>
				</li>
				<li>Click the project dropdown at the top of the page</li>
				<li>Click <strong>"New Project"</strong></li>
				<li>Enter a project name (e.g., "StorageHub Backups")</li>
				<li>Click <strong>"Create"</strong></li>
				<li>Wait for the project to be created, then select it from the dropdown</li>
			</ol>
			<div class="rounded-lg bg-slate-100 dark:bg-slate-700 p-3 text-sm">
				<strong>Tip:</strong> If you already have a Google Cloud project, you can use that instead of creating a new one.
			</div>
		</div>
	</section>

	<!-- Step 2 -->
	<section class="space-y-4">
		<h2 class="flex items-center gap-3 text-lg font-semibold text-slate-900 dark:text-white">
			<span class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm text-white">2</span>
			Enable the Google Drive API
		</h2>
		<div class="ml-11 space-y-3 text-slate-600 dark:text-slate-400">
			<ol class="list-decimal space-y-2 pl-4">
				<li>In Google Cloud Console, go to <strong>"APIs & Services"</strong> &gt; <strong>"Library"</strong></li>
				<li>Search for <strong>"Google Drive API"</strong></li>
				<li>Click on <strong>"Google Drive API"</strong> in the results</li>
				<li>Click the <strong>"Enable"</strong> button</li>
				<li>Wait for the API to be enabled</li>
			</ol>
			<div class="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 p-3 text-sm text-amber-800 dark:text-amber-200">
				<strong>Important:</strong> The API must be enabled before the service account can access Google Drive.
			</div>
		</div>
	</section>

	<!-- Step 3 -->
	<section class="space-y-4">
		<h2 class="flex items-center gap-3 text-lg font-semibold text-slate-900 dark:text-white">
			<span class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm text-white">3</span>
			Create a Service Account
		</h2>
		<div class="ml-11 space-y-3 text-slate-600 dark:text-slate-400">
			<ol class="list-decimal space-y-2 pl-4">
				<li>Go to <strong>"APIs & Services"</strong> &gt; <strong>"Credentials"</strong></li>
				<li>Click <strong>"+ Create Credentials"</strong> at the top</li>
				<li>Select <strong>"Service account"</strong></li>
				<li>Fill in the service account details:
					<ul class="mt-1 ml-4 list-disc text-sm">
						<li><strong>Name:</strong> e.g., "storagehub-backup"</li>
						<li><strong>ID:</strong> auto-generated from the name</li>
						<li><strong>Description:</strong> "Service account for StorageHub backups" (optional)</li>
					</ul>
				</li>
				<li>Click <strong>"Create and Continue"</strong></li>
				<li>Skip the "Grant this service account access" step (click <strong>"Continue"</strong>)</li>
				<li>Skip the "Grant users access" step (click <strong>"Done"</strong>)</li>
			</ol>
		</div>
	</section>

	<!-- Step 4 -->
	<section class="space-y-4">
		<h2 class="flex items-center gap-3 text-lg font-semibold text-slate-900 dark:text-white">
			<span class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm text-white">4</span>
			Generate and Download the JSON Key
		</h2>
		<div class="ml-11 space-y-3 text-slate-600 dark:text-slate-400">
			<ol class="list-decimal space-y-2 pl-4">
				<li>On the <strong>"Credentials"</strong> page, find your new service account in the list</li>
				<li>Click on the service account email to open its details</li>
				<li>Go to the <strong>"Keys"</strong> tab</li>
				<li>Click <strong>"Add Key"</strong> &gt; <strong>"Create new key"</strong></li>
				<li>Select <strong>"JSON"</strong> as the key type</li>
				<li>Click <strong>"Create"</strong></li>
				<li>A JSON file will automatically download - <strong>save this file securely!</strong></li>
			</ol>
			<div class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 p-3 text-sm text-red-800 dark:text-red-200">
				<strong>Security Warning:</strong> This JSON key grants access to your Google Drive. Keep it secure and never share it publicly. If compromised, delete the key immediately from Google Cloud Console.
			</div>
		</div>
	</section>

	<!-- Step 5 - CRITICAL -->
	<section class="space-y-4">
		<h2 class="flex items-center gap-3 text-lg font-semibold text-slate-900 dark:text-white">
			<span class="flex h-8 w-8 items-center justify-center rounded-full bg-red-600 text-sm text-white">5</span>
			Create a Shared Drive and Add the Service Account
		</h2>
		<div class="ml-11 space-y-3 text-slate-600 dark:text-slate-400">
			<div class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 p-3 text-sm text-red-800 dark:text-red-200">
				<strong>This step is CRITICAL!</strong> Without a Shared Drive, uploads will fail with "storage quota exceeded" error.
			</div>

			<h3 class="font-medium text-slate-900 dark:text-white mt-4">Create a Shared Drive:</h3>
			<ol class="list-decimal space-y-2 pl-4">
				<li>Open <a href="https://drive.google.com" target="_blank" rel="noopener noreferrer" class="text-primary-600 dark:text-primary-400 hover:underline">Google Drive</a> (make sure you're logged into your Workspace account)</li>
				<li>In the left sidebar, find <strong>"Shared drives"</strong></li>
				<li>Click <strong>"+ New"</strong> to create a new Shared Drive</li>
				<li>Name it something like "StorageHub Backups"</li>
			</ol>

			<h3 class="font-medium text-slate-900 dark:text-white mt-4">Add the Service Account as a Member:</h3>
			<ol class="list-decimal space-y-2 pl-4">
				<li>Click on your new Shared Drive to open it</li>
				<li>Click the <strong>Shared Drive name</strong> at the top, then click <strong>"Manage members"</strong></li>
				<li>
					Find your service account email address:
					<ul class="mt-1 ml-4 list-disc text-sm">
						<li>Go back to Google Cloud Console &gt; Credentials</li>
						<li>Copy the service account email (looks like: <code class="bg-slate-100 dark:bg-slate-700 px-1 rounded">name@project-id.iam.gserviceaccount.com</code>)</li>
					</ul>
				</li>
				<li>Paste the service account email in the "Add members" field</li>
				<li>Set the permission to <strong>"Content Manager"</strong> (or higher)</li>
				<li>Click <strong>"Send"</strong> (ignore the notification warning for service accounts)</li>
			</ol>

			<div class="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 p-3 text-sm text-green-800 dark:text-green-200">
				<strong>Why Shared Drives work:</strong> Files in Shared Drives are owned by the drive itself, not individual users. This means storage quota doesn't apply to the service account - files count against your organization's pooled storage instead.
			</div>
		</div>
	</section>

	<!-- Step 6 -->
	<section class="space-y-4">
		<h2 class="flex items-center gap-3 text-lg font-semibold text-slate-900 dark:text-white">
			<span class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm text-white">6</span>
			Connect StorageHub to Google Drive
		</h2>
		<div class="ml-11 space-y-3 text-slate-600 dark:text-slate-400">
			<ol class="list-decimal space-y-2 pl-4">
				<li>Go to <a href="/admin" class="text-primary-600 dark:text-primary-400 hover:underline">Admin Panel</a> &gt; <strong>Backups</strong> tab</li>
				<li>Scroll down to <strong>"Google Drive Integration"</strong></li>
				<li>Open the JSON key file you downloaded in a text editor</li>
				<li>Copy the entire contents of the file</li>
				<li>Paste it into the <strong>"Service Account JSON"</strong> text area</li>
				<li>Click <strong>"Connect to Google Drive"</strong></li>
				<li>If successful, you'll see the service account email and the Shared Drive(s) available</li>
			</ol>
		</div>
	</section>

	<!-- Troubleshooting -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-white">Troubleshooting</h2>
		<div class="space-y-4">
			<div class="rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 p-4">
				<h3 class="font-medium text-red-900">"Service Accounts do not have storage quota" error</h3>
				<p class="mt-1 text-sm text-red-800 dark:text-red-200">
					This means you're trying to upload to a regular Google Drive folder. Service accounts have zero storage quota.
					You <strong>must</strong> use a Shared Drive (Team Drive) which is only available with Google Workspace accounts.
				</p>
			</div>
			<div class="rounded-lg border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-4">
				<h3 class="font-medium text-amber-900">"No Shared Drives found" message</h3>
				<p class="mt-1 text-sm text-amber-800 dark:text-amber-200">
					Either you don't have any Shared Drives, or the service account hasn't been added as a member.
					Go back to Step 5 and make sure you've created a Shared Drive and added the service account email as a Content Manager.
				</p>
			</div>
			<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
				<h3 class="font-medium text-slate-900 dark:text-white">"API not enabled" error</h3>
				<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
					Go back to Google Cloud Console and verify that the Google Drive API is enabled for your project (Step 2).
				</p>
			</div>
			<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
				<h3 class="font-medium text-slate-900 dark:text-white">"Invalid JSON" error</h3>
				<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
					Make sure you've copied the entire contents of the JSON key file, including the opening and closing braces. Don't modify the content.
				</p>
			</div>
			<div class="rounded-lg border border-slate-200 dark:border-slate-700 p-4">
				<h3 class="font-medium text-slate-900 dark:text-white">Using a personal Gmail account?</h3>
				<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
					Unfortunately, personal Gmail accounts do not have access to Shared Drives. You'll need either:
				</p>
				<ul class="mt-2 ml-4 list-disc text-sm text-slate-600 dark:text-slate-400">
					<li>A Google Workspace account (Business, Education, etc.)</li>
					<li>Or use local backup storage instead of Google Drive</li>
				</ul>
			</div>
		</div>
	</section>

	<!-- Footer -->
	<div class="border-t border-slate-200 dark:border-slate-700 pt-6">
		<button
			on:click={() => goto('/admin')}
			class="rounded-lg bg-primary-600 px-4 py-2 text-white hover:bg-primary-700"
		>
			Back to Admin Panel
		</button>
	</div>
</div>
