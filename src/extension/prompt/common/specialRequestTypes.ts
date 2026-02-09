// Stub file for specialRequestTypes
export interface SpecialRequest {
	type: string;
	data?: unknown;
}

export const SpecialRequestTypes: any = {};

export function isContinueOnError(request: any): boolean {
	return request?.type === 'continueOnError';
}

export function isToolCallLimitAcceptance(request: any): boolean {
	return request?.type === 'toolCallLimitAcceptance';
}
