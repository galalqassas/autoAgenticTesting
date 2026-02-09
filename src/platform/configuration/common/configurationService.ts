// Configuration service stubs with dual export pattern
export interface IConfigurationService {
	get<T>(key: string): T;
	set<T>(key: string, value: T): Promise<void>;
	[key: string]: any;
}
export const IConfigurationService: any = 'IConfigurationService';

export const ConfigKey: any = {};

export enum AuthPermissionMode {
	Allow = 'allow',
	Deny = 'deny',
	Prompt = 'prompt',
	Minimal = 'minimal'
}

export enum AuthProviderId {
	GitHub = 'github',
	GitHubEnterprise = 'github-enterprise',
	Microsoft = 'microsoft'
}
