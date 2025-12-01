/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IFileSystemService } from '../../../platform/filesystem/common/fileSystemService';
import { FileType } from '../../../platform/filesystem/common/fileTypes';
import { ITelemetryService } from '../../../platform/telemetry/common/telemetry';
import { URI } from '../../../util/vs/base/common/uri';
import { IFileContent, ITestScenariosOutput } from '../common/types';

/** Directories to exclude when walking Python codebase. */
export const EXCLUDED_DIRS = new Set(['.git', '__pycache__', 'venv', '.venv', 'node_modules', '.pytest_cache', '.mypy_cache', 'dist', 'build', 'egg-info', 'tests', 'test', '__tests__']);

/**
 * Combines file contents into a single string with file path headers.
 */
export function combineFileContents(files: readonly IFileContent[]): string {
	return files.map(f => `# File: ${f.path}\n${f.content}`).join('\n\n');
}

/**
 * Extracts file paths from file contents.
 */
export function extractFilePaths(files: readonly IFileContent[]): string[] {
	return files.map(f => f.path);
}

/**
 * Reads the content of multiple files.
 */
export async function readFilesContent(
	files: readonly URI[],
	fileSystemService: IFileSystemService
): Promise<IFileContent[]> {
	const results: IFileContent[] = [];
	for (const file of files) {
		try {
			const content = await fileSystemService.readFile(file);
			results.push({
				path: file.fsPath,
				content: new TextDecoder().decode(content)
			});
		} catch {
			// File not readable, skip
		}
	}
	return results;
}

/**
 * Gathers Python files as URIs from a directory.
 */
export async function gatherPythonFileUris(
	baseUri: URI,
	targetFiles: readonly string[] | undefined,
	fileSystemService: IFileSystemService
): Promise<URI[]> {
	if (targetFiles && targetFiles.length > 0) {
		return targetFiles.map(f => URI.file(f));
	}

	const files: URI[] = [];
	await walkDirectoryForUris(baseUri, files, fileSystemService);
	return files.filter(uri =>
		uri.path.endsWith('.py') &&
		!uri.path.includes('test_') &&
		!uri.path.includes('_test.py')
	);
}

/**
 * Recursively walks a directory to find files as URIs.
 */
async function walkDirectoryForUris(
	uri: URI,
	files: URI[],
	fileSystemService: IFileSystemService
): Promise<void> {
	try {
		const entries = await fileSystemService.readDirectory(uri);
		for (const [name, type] of entries) {
			const childUri = URI.joinPath(uri, name);
			if (type === FileType.Directory) {
				if (!name.startsWith('.') && !EXCLUDED_DIRS.has(name)) {
					await walkDirectoryForUris(childUri, files, fileSystemService);
				}
			} else if (type === FileType.File) {
				files.push(childUri);
			}
		}
	} catch {
		// Directory not accessible, skip
	}
}

/**
 * Parses a JSON string containing test scenarios.
 * @throws Error if the JSON is invalid
 */
export function parseScenarios(approvedScenarios: string): ITestScenariosOutput {
	try {
		return JSON.parse(approvedScenarios) as ITestScenariosOutput;
	} catch {
		throw new Error('Invalid JSON format for approvedScenarios');
	}
}

/**
 * Gathers Python source files from a directory, excluding test files.
 * Convenience method that combines gatherPythonFileUris and readFilesContent.
 */
export async function gatherPythonFiles(
	codebaseUri: URI,
	fileSystemService: IFileSystemService
): Promise<IFileContent[]> {
	const uris = await gatherPythonFileUris(codebaseUri, undefined, fileSystemService);
	return readFilesContent(uris, fileSystemService);
}

/**
 * Telemetry event types for Python testing tools.
 */
export type PythonTestTelemetryEvent =
	| 'pythonTestGenerationToolInvoked'
	| 'pythonTestImplementationToolInvoked'
	| 'pythonTestEvaluationToolInvoked';

/**
 * Base telemetry properties shared across all Python testing tools.
 */
export interface IBaseTelemetryProps {
	requestId: string | undefined;
}

/**
 * Sends telemetry for Python test generation tool.
 */
export function sendTestGenerationTelemetry(
	telemetryService: ITelemetryService,
	requestId: string | undefined,
	scenarioCount: number
): void {
	/* __GDPR__
		"pythonTestGenerationToolInvoked" : {
			"owner": "copilot",
			"requestId": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "The id of the current request turn." },
			"scenarioCount": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "Number of test scenarios identified" }
		}
	*/
	telemetryService.sendMSFTTelemetryEvent('pythonTestGenerationToolInvoked', {
		requestId,
		scenarioCount: String(scenarioCount)
	});
}

/**
 * Sends telemetry for Python test implementation tool.
 */
export function sendTestImplementationTelemetry(
	telemetryService: ITelemetryService,
	requestId: string | undefined,
	scenarioCount: number
): void {
	/* __GDPR__
		"pythonTestImplementationToolInvoked" : {
			"owner": "copilot",
			"requestId": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "The id of the current request turn." },
			"scenarioCount": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "Number of test scenarios implemented" }
		}
	*/
	telemetryService.sendMSFTTelemetryEvent('pythonTestImplementationToolInvoked', {
		requestId,
		scenarioCount: String(scenarioCount)
	});
}

/**
 * Sends telemetry for Python test evaluation tool.
 */
export function sendTestEvaluationTelemetry(
	telemetryService: ITelemetryService,
	requestId: string | undefined,
	totalTests: number,
	passedTests: number,
	coverage: number,
	securityIssueCount: number
): void {
	/* __GDPR__
		"pythonTestEvaluationToolInvoked" : {
			"owner": "copilot",
			"requestId": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "The id of the current request turn." },
			"totalTests": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "Total number of tests" },
			"passedTests": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "Number of passed tests" },
			"coverage": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "Code coverage percentage" },
			"securityIssueCount": { "classification": "SystemMetaData", "purpose": "FeatureInsight", "comment": "Number of security issues found" }
		}
	*/
	telemetryService.sendMSFTTelemetryEvent('pythonTestEvaluationToolInvoked', {
		requestId,
		totalTests: String(totalTests),
		passedTests: String(passedTests),
		coverage: String(coverage),
		securityIssueCount: String(securityIssueCount)
	});
}
