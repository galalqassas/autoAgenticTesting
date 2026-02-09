// OpenAI types and values stub file

export const OpenAI = {
    ChatCompletionContentPart: {} as any,
    ChatCompletionContentPartText: {} as any
};
export type ChatCompletionContentPart = any;
export type ChatCompletionContentPartText = any;

// Dual export pattern: interface for type usage, const for value usage
export interface IChatEndpointInfo { [key: string]: any; }
export const IChatEndpointInfo: any = {};

export interface APIErrorResponse {
	error?: { message?: string; code?: string; type?: string };
	status?: number;
}
export const APIErrorResponse: any = {};

export interface APIUsage {
	prompt_tokens?: number;
	completion_tokens?: number;
	total_tokens?: number;
}
export const APIUsage: any = {};

export enum FilterReason {
	Copyright = 'copyright',
	Prompt = 'prompt',
	Response = 'response',
	Unknown = 'unknown'
}

export interface ChatCompletion {
	id?: string;
	object?: string;
	created?: number;
	model?: string;
	choices?: any[];
	usage?: APIUsage;
}
export const ChatCompletion: any = {};

export type RawMessageConversionCallback = (message: any) => any;
export const RawMessageConversionCallback: any = {};

export const rawMessageToCAPI: any = () => {};

// Additional networking types exported as both interface and const
export interface OpenAiFunctionTool {
	type: 'function';
	function: { name: string; description?: string; parameters?: any };
}
export const OpenAiFunctionTool: any = {};

export interface OpenAiResponsesFunctionTool extends OpenAiFunctionTool {}
export const OpenAiResponsesFunctionTool: any = {};

export interface AnthropicMessagesTool {
	name: string;
	description?: string;
	input_schema?: any;
}
export const AnthropicMessagesTool: any = {};

export interface Prediction {
	type: string;
	content?: any;
}
export const Prediction: any = {};

export interface OptionalChatRequestParams {
	temperature?: number;
	top_p?: number;
	max_tokens?: number;
	stream?: boolean;
	[key: string]: any;
}
export const OptionalChatRequestParams: any = {};

export type FinishedCallback = (result: any) => void;
export const FinishedCallback: any = {};

export interface Source {
	type: string;
	uri?: string;
	[key: string]: any;
}
export const Source: any = {};

export interface TelemetryData {
	[key: string]: any;
}
export const TelemetryData: any = {};

export interface IResponseDelta {
	content?: string;
	[key: string]: any;
}
export const IResponseDelta: any = {};

export interface CapturingToken {
	cancel(): void;
	[key: string]: any;
}
export const CapturingToken: any = {};

export type RequestId = string;
export const RequestId: any = {};
