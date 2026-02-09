// Stub file for copilotTokenStore - dual export pattern for DI
export interface ICopilotTokenStore {
	getToken(): Promise<any>;
	setToken(token: any): void;
	clearToken(): void;
	[key: string]: any;
}
export const ICopilotTokenStore: any = 'ICopilotTokenStore';
export const CopilotTokenStore: any = {};
