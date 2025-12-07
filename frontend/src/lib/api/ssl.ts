/**
 * SSL API client for StorageHub.
 */

import { get, patch, post } from './client';

export type SSLMode = 'disabled' | 'self_signed' | 'letsencrypt';

export interface SSLConfig {
	id: string;
	mode: SSLMode;
	domain: string | null;
	email: string | null;
	certificate_valid: boolean;
	certificate_expiry: string | null;
	last_renewal_attempt: string | null;
	last_error: string | null;
	auto_renew: boolean;
	created_at: string;
	updated_at: string;
}

export interface SSLStatus {
	mode: SSLMode;
	enabled: boolean;
	certificate_valid: boolean;
	certificate_expiry: string | null;
	days_until_expiry: number | null;
	domain: string | null;
	last_error: string | null;
}

export interface SSLConfigUpdate {
	mode: SSLMode;
	domain?: string | null;
	email?: string | null;
	auto_renew?: boolean;
}

export interface GenerateCertificateRequest {
	mode: SSLMode;
	domain?: string | null;
	email?: string | null;
}

export interface CertificateActionResponse {
	success: boolean;
	message: string;
	certificate_valid: boolean;
	certificate_expiry: string | null;
}

/**
 * Get current SSL configuration.
 */
export async function getSSLConfig(): Promise<SSLConfig> {
	return get<SSLConfig>('/ssl');
}

/**
 * Get SSL status.
 */
export async function getSSLStatus(): Promise<SSLStatus> {
	return get<SSLStatus>('/ssl/status');
}

/**
 * Update SSL configuration.
 */
export async function updateSSLConfig(data: SSLConfigUpdate): Promise<SSLConfig> {
	return patch<SSLConfig>('/ssl', data);
}

/**
 * Generate or request a new certificate.
 */
export async function generateCertificate(data: GenerateCertificateRequest): Promise<CertificateActionResponse> {
	return post<CertificateActionResponse>('/ssl/generate', data);
}

/**
 * Renew Let's Encrypt certificate.
 */
export async function renewCertificate(): Promise<CertificateActionResponse> {
	return post<CertificateActionResponse>('/ssl/renew');
}

/**
 * Test current certificate validity.
 */
export async function testCertificate(): Promise<CertificateActionResponse> {
	return post<CertificateActionResponse>('/ssl/test');
}
