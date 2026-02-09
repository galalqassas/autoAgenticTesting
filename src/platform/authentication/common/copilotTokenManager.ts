// Stub file for copilotTokenManager - dual export pattern for DI
export interface ICopilotTokenManager {
	getToken(): Promise<any>;
	refreshToken(): Promise<any>;
	[key: string]: any;
}
export const ICopilotTokenManager: any = 'ICopilotTokenManager';
export const CopilotTokenManager: any = {};
