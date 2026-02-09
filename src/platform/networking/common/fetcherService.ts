// Stub file for fetcherService

export type FetcherId = string;

export interface FetchOptions {
	method?: string;
	headers?: Record<string, string>;
	body?: string | ArrayBuffer;
	timeout?: number;
	signal?: AbortSignal;
	json?: any;
	useFetcher?: FetcherId;
	suppressIntegrationId?: boolean;
}

export interface IAbortController {
	signal: AbortSignal;
	abort(): void;
}

// Make PaginationOptions generic with T parameter
export interface PaginationOptions<T = any> {
	page?: number;
	perPage?: number;
	mapResult?: (item: any) => T;
}

export interface Response {
	ok: boolean;
	status: number;
	statusText: string;
	headers: Headers;
	json(): Promise<any>;
	text(): Promise<string>;
	arrayBuffer(): Promise<ArrayBuffer>;
}

export interface IFetcher {
	getUserAgentLibrary(): string;
	disconnectAll(): Promise<unknown>;
	makeAbortController(): IAbortController;
	isAbortError(error: unknown): boolean;
	isInternetDisconnectedError(error: unknown): boolean;
	isFetcherError(error: unknown): boolean;
	getUserMessageForFetcherError(error: unknown): string;
	fetchWithPagination<T>(url: string, options?: PaginationOptions<T>): Promise<T[]>;
	fetch(url: string, options?: FetchOptions): Promise<Response>;
	proxyFetch?(url: string, options?: FetchOptions): Promise<Response>;
	setProxy?(proxy: string): void;
	clearProxy?(): void;
}

export interface IFetcherService extends IFetcher {}

export const FetcherService: any = {};
