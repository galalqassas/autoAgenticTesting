/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';

// --- Extension Activation ---

export function activate(context: vscode.ExtensionContext) {
	console.log('Agentic Testing extension is now active!');

	// Register Command
	const disposable = vscode.commands.registerCommand('agentic-testing.generateTests', async () => {
		
        // Prompt for codebase path
        const folders = vscode.workspace.workspaceFolders;
        const defaultUri = folders ? folders[0].uri : undefined;

        const folderUri = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            defaultUri: defaultUri,
            openLabel: 'Select Codebase to Test'
        });

        if (!folderUri || folderUri.length === 0) {
            return;
        }
        
        const codebasePath = folderUri[0].fsPath;

		await vscode.window.withProgress({
			location: vscode.ProgressLocation.Notification,
			title: "Generating Tests...",
			cancellable: true
		}, async (progress, _token) => {
			try {
				progress.report({ message: 'Analyzing codebase...' });
				
				// For now, show a message that the pipeline would run here
				// The full pipeline integration can be added once the basic extension works
				vscode.window.showInformationMessage(
					`Would generate tests for: ${codebasePath}\n\nNote: Full pipeline integration pending.`
				);
				
			} catch (err) {
				vscode.window.showErrorMessage(`Error: ${err instanceof Error ? err.message : String(err)}`);
			}
		});
	});

	context.subscriptions.push(disposable);
}

export function deactivate() {}
