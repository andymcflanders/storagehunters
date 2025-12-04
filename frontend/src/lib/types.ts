/**
 * TypeScript types for StorageHub.
 */

// User types
export interface User {
	id: string;
	name: string;
	email: string | null;
	avatar_url: string | null;
	requires_password: boolean;
	created_at: string;
	updated_at: string;
}

export interface UserCreate {
	name: string;
	email?: string;
	requires_password?: boolean;
	password?: string;
}

export interface UserUpdate {
	name?: string;
	email?: string;
	requires_password?: boolean;
	password?: string;
}

export interface SessionResponse {
	token: string;
	expires_at: string;
	user: User;
}

// Location types
export interface Location {
	id: string;
	name: string;
	description: string | null;
	address: string | null;
	sort_order: number;
	created_at: string;
	updated_at: string;
}

export interface LocationCreate {
	name: string;
	description?: string;
	address?: string;
	sort_order?: number;
}

export interface LocationUpdate {
	name?: string;
	description?: string;
	address?: string;
	sort_order?: number;
}

export interface ContainerSummary {
	id: string;
	name: string;
	qr_code: string;
	item_count: number;
}

export interface LocationWithContainers extends Location {
	containers: ContainerSummary[];
}

// Container types
export interface Container {
	id: string;
	name: string;
	location_id: string;
	parent_container_id: string | null;
	qr_code: string;
	notes: string | null;
	created_at: string;
	updated_at: string;
}

export interface ContainerCreate {
	name: string;
	location_id: string;
	parent_container_id?: string;
	notes?: string;
}

export interface ContainerUpdate {
	name?: string;
	location_id?: string;
	parent_container_id?: string;
	notes?: string;
}

export interface ItemSummary {
	id: string;
	name: string;
	thumbnail_url: string | null;
}

export interface PathElement {
	id: string;
	name: string;
	type: 'location' | 'container';
}

export interface ContainerWithItems extends Container {
	items: ItemSummary[];
	child_containers: Container[];
	path: PathElement[];
}

// Item types
export type Condition = 'good' | 'fair' | 'damaged' | 'needs_repair';
export type Seasonal = 'none' | 'spring' | 'summer' | 'fall' | 'winter' | 'holiday';

export interface Item {
	id: string;
	name: string;
	description: string | null;
	container_id: string;
	owner_id: string | null;
	size: string | null;
	condition: Condition;
	seasonal: Seasonal;
	value_estimate: number | null;
	created_at: string;
	updated_at: string;
}

export interface ItemCreate {
	name: string;
	description?: string;
	container_id: string;
	owner_id?: string;
	size?: string;
	condition?: Condition;
	seasonal?: Seasonal;
	value_estimate?: number;
}

export interface ItemUpdate {
	name?: string;
	description?: string;
	container_id?: string;
	owner_id?: string;
	size?: string;
	condition?: Condition;
	seasonal?: Seasonal;
	value_estimate?: number;
}

export interface ItemImage {
	id: string;
	filename: string;
	filepath: string;
	ai_tags: string[];
	ai_description: string | null;
	ai_processed: boolean;
	created_at: string;
}

export interface Tag {
	id: string;
	name: string;
}

export interface OwnerInfo {
	id: string;
	name: string;
	avatar_url: string | null;
}

export interface ItemWithDetails extends Item {
	images: ItemImage[];
	tags: Tag[];
	owner: OwnerInfo | null;
	path: PathElement[];
	related_items: Item[];
}

// Printer types
export type PrinterType = 'zebra_zpl' | 'brother_ql' | 'generic_pdf';
export type ConnectionType = 'network' | 'usb' | 'file';

export interface Printer {
	id: string;
	name: string;
	printer_type: PrinterType;
	connection_type: ConnectionType;
	address: string;
	label_width_mm: number;
	label_height_mm: number;
	is_default: boolean;
	created_at: string;
	updated_at: string;
}

export interface PrinterCreate {
	name: string;
	printer_type: PrinterType;
	connection_type: ConnectionType;
	address: string;
	label_width_mm?: number;
	label_height_mm?: number;
	is_default?: boolean;
}

export interface PrinterUpdate {
	name?: string;
	printer_type?: PrinterType;
	connection_type?: ConnectionType;
	address?: string;
	label_width_mm?: number;
	label_height_mm?: number;
	is_default?: boolean;
}

export interface PrintResult {
	success: boolean;
	message: string;
}

export interface PrintPreviewResult {
	preview_url: string;
}
