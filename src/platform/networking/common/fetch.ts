// Fetch types with dual export pattern (interface + const)

export const Fetch: any = {};

export interface AnthropicMessagesTool {
	name: string;
	description?: string;
	input_schema?: any;
}
export const AnthropicMessagesTool: any = {};

export type FinishedCallback = (result: any) => void;
export const FinishedCallback: any = {};

export interface OpenAiFunctionTool {
	type: 'function';
	function: { name: string; description?: string; parameters?: any };
}
export const OpenAiFunctionTool: any = {};

export interface OpenAiResponsesFunctionTool extends OpenAiFunctionTool {}
export const OpenAiResponsesFunctionTool: any = {};

export interface OptionalChatRequestParams {
	temperature?: number;
	top_p?: number;
	max_tokens?: number;
	stream?: boolean;
	tool_choice?: any;
	[key: string]: any;
}
export const OptionalChatRequestParams: any = {};

export interface Prediction {
	type: string;
	content?: any;
}
export const Prediction: any = {};

export type RequestId = string;
export const RequestId: any = {};

export interface IResponseDelta {
	content?: string;
	finish_reason?: string;
	[key: string]: any;
}
export const IResponseDelta: any = {};
