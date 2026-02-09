// Type augmentation for missing VS Code API types
// These types are used in the codebase but not yet in the stable vscode typings

import * as vscode from 'vscode';

declare module 'vscode' {
	// Missing chat-related types
	export interface ChatRequestEditedFileEvent {
		uri: vscode.Uri;
		oldContent?: string;
		newContent?: string;
	}

	export interface ChatRequestModeInstructions {
		mode: string;
		instructions: string;
	}

	export interface ChatCommand {
		name: string;
		description: string;
	}

	// Augment ChatRequest with missing properties
	export interface ChatRequest {
		editedFileEvents?: ChatRequestEditedFileEvent[];
		acceptedConfirmationData?: unknown;
	}

	// Augment ChatPromptReference with missing properties
	export interface ChatPromptReference {
		name?: string;
		isReadonly?: boolean;
	}

	// Augment LanguageModelToolInvocationOptions with missing properties
	export interface LanguageModelToolInvocationOptions<T> {
		chatRequestId?: string;
	}

	// Augment ChatErrorDetails with missing properties
	export interface ChatErrorDetails {
		code?: string;
		level?: import('./vscodeTypes').ChatErrorLevel;
		isQuotaExceeded?: boolean;
		isRateLimited?: boolean;
		responseIsFiltered?: boolean;
	}

	// Augment PreparedToolInvocation with missing properties
	export interface PreparedToolInvocation {
		pastTenseMessage?: vscode.MarkdownString | vscode.LanguageModelTextPart[];
	}
}
