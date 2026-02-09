// Stub file for commandService
import * as vscode from 'vscode';

export interface ICommandService {
	executeCommand<T>(command: string, ...args: any[]): Thenable<T | undefined>;
	getCommand(commandId: string): any;
}

export const CommandService: any = {};
export const ICommandService: any = {};
