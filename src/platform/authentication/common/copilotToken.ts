export interface CopilotToken {
	token: string;
	expiresAt: number;
	refresh_in?: number;
	organization_list?: string[];
	annotations_enabled?: boolean;
	isInternal?: boolean;
	isVscodeTeamMember?: boolean;
}

export const CopilotToken: any = {};
