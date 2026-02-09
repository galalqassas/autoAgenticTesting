import * as promptTsx from '@vscode/prompt-tsx';

declare module '@vscode/prompt-tsx' {
    export namespace Raw {
        export type ChatRole = 'user' | 'assistant' | 'system';
        export const ChatRole: any;
        export interface ChatCompletionContentPart { [key: string]: any; }
        export const ChatCompletionContentPart: any;
        export class ChatMessage { [key: string]: any; }
        export const ChatCompletionContentPartText: any;
        export const ChatCompletionContentPartKind: any;
    }
    export const Raw: any;
    export namespace OutputMode {
        export type Raw = any;
        export const Raw: any;
        export const JustText: any;
        export const OpenAI: any;
    }
    export const OutputMode: any;
    export namespace JSONTree {
        export type PromptElementJSON = any;
    }
    export const toMode: <T = any>(...args: any[]) => any; // generic function
    export const OpenAI: any;
    export namespace OpenAI {
         export type ChatCompletionContentPart = any;
    }
    export class PromptElement<P = any, S = any> { 
        constructor(props: P);
        props: P;
        static props: any;
        [key: string]: any;
        render(context: any, token: any): any;
        prepare(context: any): any;
        createElement(ctor: any, props: any): any;
    }
    
    export const UserMessage: any;
    export const AssistantMessage: any;
    export const SystemMessage: any;
    export const ToolMessage: any;
    export const Prioritized: any;
    export const PromptPiece: any;
    export const PromptSizing: any;
    export class HTMLTracer { [key: string]: any; }
    export interface ITokenizer<T = any> { [key: string]: any; }
    export const JSONTree: any;
    export class MetadataMap { [key: string]: any; }
    export const QueueItem: any;
    export class RenderPromptResult<T = any> { [key: string]: any; }
    export interface BasePromptElementProps { [key: string]: any; }
    export const TextChunk: any;
    export const useKeepWith: any;
    export class PromptReference { 
        constructor(...args: any[]);
        [key: string]: any; 
    }
    export class PromptRenderer<P = any, M = any> { 
        [key: string]: any;
        constructor(...args: any[]);
        render(progress?: any, token?: any, opts?: any): Promise<any>;
        createElement(element: any, ...args: any[]): any;
    }
    export const IChatEndpointInfo: any;
}
