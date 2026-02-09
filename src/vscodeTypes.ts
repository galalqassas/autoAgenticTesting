/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as vscode from 'vscode';

export import Position = vscode.Position;
export import Range = vscode.Range;
export import Selection = vscode.Selection;
export import EventEmitter = vscode.EventEmitter;
export import CancellationTokenSource = vscode.CancellationTokenSource;
export import Diagnostic = vscode.Diagnostic;
export import TextEdit = vscode.TextEdit;
export import WorkspaceEdit = vscode.WorkspaceEdit;
export import Uri = vscode.Uri;
export import MarkdownString = vscode.MarkdownString;
export import TextEditorCursorStyle = vscode.TextEditorCursorStyle;
export import TextEditorLineNumbersStyle = vscode.TextEditorLineNumbersStyle;
export import TextEditorRevealType = vscode.TextEditorRevealType;
export import EndOfLine = vscode.EndOfLine;
export import DiagnosticSeverity = vscode.DiagnosticSeverity;
export import ExtensionMode = vscode.ExtensionMode;
export import Location = vscode.Location;
export import DiagnosticRelatedInformation = vscode.DiagnosticRelatedInformation;

// Stubbing missing types
export type ChatVariableLevel = any;
export type ChatResponseClearToPreviousToolInvocationReason = any;
export type ChatResponseMarkdownPart = any;
export type ChatResponseThinkingProgressPart = any;
export type ChatResponseFileTreePart = any;
export type ChatResponseAnchorPart = any;
export type ChatResponseProgressPart = any;
export type ChatResponseProgressPart2 = any;
export type ChatResponseReferencePart = any;
export type ChatResponseReferencePart2 = any;
export type ChatResponseCodeCitationPart = any;
export type ChatResponseCommandButtonPart = any;
export type ChatResponseWarningPart = any;
export type ChatResponseMovePart = any;
export type ChatResponseExtensionsPart = any;
export type ChatResponseExternalEditPart = any;
export type ChatResponsePullRequestPart = any;
export type ChatResponseMarkdownWithVulnerabilitiesPart = any;
export type ChatResponseCodeblockUriPart = any;
export type ChatResponseTextEditPart = any;
export type ChatResponseNotebookEditPart = any;
export type ChatResponseConfirmationPart = any;
export type ChatPrepareToolInvocationPart = any;
export type ChatRequest = any;
export type ChatRequestTurn = any;
export type ChatResponseTurn = any;
export type NewSymbolName = any;
export type NewSymbolNameTag = any;
export type NewSymbolNameTriggerKind = any;
export type ChatLocation = any;
export type ChatRequestEditorData = any;
export type ChatRequestNotebookData = any;
export type LanguageModelToolInformation = any;

// Class implementations for types used with `new`
export class LanguageModelToolResult {
	constructor(public readonly content: any[]) {}
}

export class ExtendedLanguageModelToolResult extends LanguageModelToolResult {}
export type LanguageModelToolResult2 = any;
export type SymbolInformation = any;

export class LanguageModelPromptTsxPart {
	constructor(public readonly value: any) {}
}

export class LanguageModelTextPart {
	constructor(public readonly value: string) {}
}

export type LanguageModelTextPart2 = any;
export type LanguageModelThinkingPart = any;
export type LanguageModelDataPart = any;
export type LanguageModelDataPart2 = any;
export type LanguageModelPartAudience = any;
export type LanguageModelToolMCPSource = any;
export type LanguageModelToolExtensionSource = any;
export type ChatReferenceBinaryData = any;
export type ChatReferenceDiagnostic = any;
export type TextSearchMatch2 = any;
export type AISearchKeyword = any;
export type ExcludeSettingOptions = any;
export type NotebookCellKind = any;
export type NotebookRange = any;
export type NotebookEdit = any;
export type NotebookCellData = any;
export type NotebookData = any;

// ChatErrorLevel as an enum for value usage
export enum ChatErrorLevel {
	Info = 'info',
	Warning = 'warning',
	Error = 'error'
}

export type TerminalShellExecutionCommandLineConfidence = any;
export type ChatRequestEditedFileEventKind = any;
export type Extension = any;
export type LanguageModelToolCallPart = any;
export type LanguageModelToolResultPart = any;
export type LanguageModelToolResultPart2 = any;
export type LanguageModelChatMessageRole = any;
export type LanguageModelChatMessage = any;
export type LanguageModelChatToolMode = any;
export type TextEditorSelectionChangeKind = any;
export type TextDocumentChangeReason = any;
export type ChatToolInvocationPart = any;
export type ChatResponseTurn2 = any;
export type ChatRequestTurn2 = any;
export type LanguageModelError = any;
export type SymbolKind = any;
export type SnippetString = any;
export type SnippetTextEdit = any;
export type FileType = any;
export type ChatRequestEditedFileEvent = any;
export type ChatPromptReference = any;
export type ChatSessionStatus = any;

export const l10n = {
	/**
	 * @deprecated Only use this import in tests. For the actual extension,
	 * use `import { l10n } from 'vscode'` or `import * as l10n from '@vscode/l10n'`.
	 */
	t: vscode.l10n.t
};

export const authentication = {
	getSession: vscode.authentication.getSession,
};
