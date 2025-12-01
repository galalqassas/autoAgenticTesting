/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { ChatFetchResponseType, ChatLocation } from '../../../platform/chat/common/commonTypes';
import { IEndpointProvider } from '../../../platform/endpoint/common/endpointProvider';
import { IFileSystemService } from '../../../platform/filesystem/common/fileSystemService';
import { CancellationToken } from '../../../util/vs/base/common/cancellation';
import { URI } from '../../../util/vs/base/common/uri';
import { IInstantiationService } from '../../../util/vs/platform/instantiation/common/instantiation';
import { PromptRenderer } from '../../prompts/node/base/promptRenderer';
import { IPythonTestingPipelineService } from '../common/pythonTestingPipelineService';
import {
	IFileContent,
	IPipelineState,
	IPyTestExecutionResult,
	IPythonTestingPipelineOptions,
	ISecurityIssue,
	ITestEvaluationOutput,
	ITestImplementationResult,
	ITestScenariosOutput,
} from '../common/types';
import { TestCaseEvaluationPrompt } from './prompts/testCaseEvaluationPrompt';
import { TestCaseIdentificationPrompt } from './prompts/testCaseIdentificationPrompt';
import { TestCaseImplementationPrompt } from './prompts/testCaseImplementationPrompt';
import { combineFileContents, extractFilePaths, gatherPythonFileUris, readFilesContent } from './toolUtils';

/**
 * Implementation of the Python Testing Pipeline Service.
 * Orchestrates three specialized agents for automated test generation.
 */
export class PythonTestingPipelineService implements IPythonTestingPipelineService {
	declare readonly _serviceBrand: undefined;

	constructor(
		@IEndpointProvider private readonly endpointProvider: IEndpointProvider,
		@IInstantiationService private readonly instantiationService: IInstantiationService,
		@IFileSystemService private readonly fileSystemService: IFileSystemService,
	) { }

	/**
	 * Runs the complete testing pipeline with coverage improvement loop.
	 */
	async runPipeline(options: IPythonTestingPipelineOptions, token: CancellationToken): Promise<IPipelineState> {
		const state: IPipelineState = { status: 'pending_identification', iteration: 0 };
		const targetCoverage = options.targetCoverage ?? 90;
		const maxIterations = options.maxIterations ?? 20;

		try {
			// Step 1: Identify test scenarios
			state.status = 'pending_identification';
			const identifiedScenarios = await this.identifyTestScenarios(
				options.codebasePath,
				options.targetFiles,
				token
			);
			state.identifiedScenarios = identifiedScenarios;

			// Step 2: Request human approval
			state.status = 'awaiting_approval';
			const approvedScenarios = await this.requestApproval(identifiedScenarios, token);
			state.approvedScenarios = approvedScenarios;

			// Step 3: Generate initial test code
			state.status = 'generating_tests';
			const testOutputDir = options.testOutputDir || options.codebasePath;
			let implementation = await this.generateTestCode(
				approvedScenarios,
				options.codebasePath,
				testOutputDir,
				token
			);
			state.generatedTestCode = implementation.testCode;
			state.testFilePath = implementation.filePath;

			// Step 4-6: Run tests and improvement loop
			if (options.autoRunTests ?? true) {
				let currentCoverage = 0;
				let hasSevereSecurityIssues = false;

				while (state.iteration! < maxIterations) {
					state.iteration = (state.iteration ?? 0) + 1;

					// Run tests
					state.status = 'running_tests';
					const testResult = await this.runTests(
						implementation.filePath,
						options.codebasePath,
						token
					);

					// Evaluate results
					state.status = 'evaluating_results';
					const sourceFiles = await gatherPythonFileUris(URI.file(options.codebasePath), undefined, this.fileSystemService);
					const fileContents = await readFilesContent(sourceFiles, this.fileSystemService);
					const evaluation = await this.evaluateResults(
						testResult,
						approvedScenarios,
						fileContents,
						token
					);
					state.evaluationResult = evaluation;

					currentCoverage = evaluation.code_coverage_percentage;
					hasSevereSecurityIssues = evaluation.has_severe_security_issues;

					// Check completion criteria
					const coverageMet = currentCoverage >= targetCoverage;
					const securityMet = !hasSevereSecurityIssues;

					if (coverageMet && securityMet) {
						break;
					}

					// Generate additional tests to improve
					state.status = 'improving_coverage';
					const uncoveredAreas = this.extractUncoveredAreas(testResult.stdout);
					const severeIssues = evaluation.security_issues.filter(
						si => si.severity === 'critical' || si.severity === 'high'
					);

					implementation = await this.generateAdditionalTests(
						options.codebasePath,
						implementation.filePath,
						currentCoverage,
						uncoveredAreas,
						severeIssues,
						token
					);
					state.generatedTestCode = implementation.testCode;
				}
			}

			state.status = 'completed';
			return state;

		} catch (error) {
			state.status = 'failed';
			state.error = error instanceof Error ? error.message : String(error);
			return state;
		}
	}

	/**
	 * Agent 1: Identifies test scenarios from the codebase.
	 */
	async identifyTestScenarios(
		codebasePath: string,
		targetFiles: readonly string[] | undefined,
		token: CancellationToken
	): Promise<ITestScenariosOutput> {
		const codebaseUri = URI.file(codebasePath);
		const pythonFiles = await gatherPythonFileUris(codebaseUri, targetFiles, this.fileSystemService);

		if (pythonFiles.length === 0) {
			throw new Error('No Python files found in the specified path');
		}

		const fileContents = await readFilesContent(pythonFiles, this.fileSystemService);
		const combinedContent = combineFileContents(fileContents);
		const filePaths = extractFilePaths(fileContents);

		const endpoint = await this.endpointProvider.getChatEndpoint('copilot-fast');
		const promptRenderer = PromptRenderer.create(
			this.instantiationService,
			endpoint,
			TestCaseIdentificationPrompt,
			{ codeContent: combinedContent, filePaths }
		);

		const prompt = await promptRenderer.render();
		const response = await endpoint.makeChatRequest(
			'pythonTestIdentification',
			prompt.messages,
			undefined,
			token,
			ChatLocation.Other
		);

		if (response.type !== ChatFetchResponseType.Success) {
			throw new Error(`Failed to identify test scenarios: ${response.reason}`);
		}

		return this.parseJsonResponse<ITestScenariosOutput>(response.value, 'test_scenarios');
	}

	/**
	 * Requests human approval for identified scenarios.
	 * In a real implementation, this would show a UI for user interaction.
	 */
	async requestApproval(
		scenarios: ITestScenariosOutput,
		_token: CancellationToken
	): Promise<ITestScenariosOutput> {
		// Placeholder - in a real implementation, show UI dialog
		return scenarios;
	}

	/**
	 * Agent 2: Generates PyTest test code from approved scenarios.
	 */
	async generateTestCode(
		scenarios: ITestScenariosOutput,
		codebasePath: string,
		outputDir: string,
		token: CancellationToken
	): Promise<ITestImplementationResult> {
		const codebaseUri = URI.file(codebasePath);
		const pythonFiles = await gatherPythonFileUris(codebaseUri, undefined, this.fileSystemService);
		const fileContents = await readFilesContent(pythonFiles, this.fileSystemService);
		const combinedContext = combineFileContents(fileContents);
		const filePaths = extractFilePaths(fileContents);

		const endpoint = await this.endpointProvider.getChatEndpoint('copilot-fast');
		const promptRenderer = PromptRenderer.create(
			this.instantiationService,
			endpoint,
			TestCaseImplementationPrompt,
			{ scenarios, codeContext: combinedContext, filePaths }
		);

		const prompt = await promptRenderer.render();
		const response = await endpoint.makeChatRequest(
			'pythonTestImplementation',
			prompt.messages,
			undefined,
			token,
			ChatLocation.Other
		);

		if (response.type !== ChatFetchResponseType.Success) {
			throw new Error(`Failed to generate test code: ${response.reason}`);
		}

		let testCode = this.sanitizeCode(response.value);

		// Validate and fix syntax if needed
		for (let attempt = 0; attempt < 3; attempt++) {
			const { valid, error } = this.validatePythonSyntax(testCode);
			if (valid) {
				break;
			}
			testCode = await this.fixSyntaxError(testCode, error, codebasePath, token);
		}

		// Write the test file
		const testFileName = `test_generated_${Date.now()}.py`;
		const testFilePath = URI.joinPath(URI.file(outputDir), testFileName);
		await this.fileSystemService.writeFile(testFilePath, new TextEncoder().encode(testCode));

		return {
			testCode,
			filePath: testFilePath.fsPath,
			scenarioCount: scenarios.test_scenarios.length
		};
	}

	/**
	 * Runs the generated PyTest suite with coverage measurement.
	 */
	async runTests(
		testFilePath: string,
		codebasePath: string,
		_token: CancellationToken
	): Promise<IPyTestExecutionResult> {
		const cp = await import('child_process');
		const pythonCommand = process.env.PYTHON ?? 'python';
		const args = [
			'-m', 'pytest',
			testFilePath,
			'-v', '--tb=short',
			`--cov=${codebasePath}`,
			'--cov-report=term-missing',
			'--cov-report=json',
		];

		try {
			const result = cp.spawnSync(pythonCommand, args, {
				shell: true,
				encoding: 'utf-8',
				cwd: URI.file(testFilePath).with({ path: URI.file(testFilePath).path.replace(/\/[^/]+$/, '') }).fsPath,
				timeout: 300000, // 5 minutes
			});

			const stdout = result.stdout ?? '';
			const stderr = result.stderr ?? '';
			const exitCode = typeof result.status === 'number' ? result.status : 1;

			// Parse test results
			const testCounts = this.parseTestCounts(stdout);
			const coveragePercentage = await this.parseCoverageJson(testFilePath);

			return {
				exitCode,
				stdout,
				stderr,
				totalTests: testCounts.total,
				passed: testCounts.passed,
				failed: testCounts.failed,
				coveragePercentage,
			};
		} catch (e) {
			return {
				exitCode: 1,
				stdout: '',
				stderr: `Failed to run tests: ${e instanceof Error ? e.message : String(e)}`,
				totalTests: 0,
				passed: 0,
				failed: 0,
				coveragePercentage: 0,
			};
		}
	}

	/**
	 * Agent 3: Evaluates test results, coverage, and performs security analysis.
	 */
	async evaluateResults(
		testResult: IPyTestExecutionResult,
		scenarios: ITestScenariosOutput,
		sourceCode: readonly IFileContent[],
		token: CancellationToken
	): Promise<ITestEvaluationOutput> {
		const sourceCodeStr = combineFileContents(sourceCode);

		const endpoint = await this.endpointProvider.getChatEndpoint('copilot-fast');
		const promptRenderer = PromptRenderer.create(
			this.instantiationService,
			endpoint,
			TestCaseEvaluationPrompt,
			{
				testResult,
				approvedScenarios: scenarios,
				sourceCode: sourceCodeStr,
			}
		);

		const prompt = await promptRenderer.render();
		const response = await endpoint.makeChatRequest(
			'pythonTestEvaluation',
			prompt.messages,
			undefined,
			token,
			ChatLocation.Other
		);

		if (response.type !== ChatFetchResponseType.Success) {
			throw new Error(`Failed to evaluate test results: ${response.reason}`);
		}

		try {
			const data = this.parseJsonResponse<{
				execution_summary: { total_tests: number; passed: number; failed: number };
				code_coverage_percentage: number;
				actionable_recommendations: string[];
				security_issues?: Array<{ severity: string; issue: string; location: string; recommendation: string }>;
				has_severe_security_issues?: boolean;
			}>(response.value, 'execution_summary');

			const securityIssues: ISecurityIssue[] = (data.security_issues ?? []).map(si => ({
				severity: si.severity as ISecurityIssue['severity'],
				issue: si.issue,
				location: si.location,
				recommendation: si.recommendation,
			}));

			const hasSevere = data.has_severe_security_issues ??
				securityIssues.some(si => si.severity === 'critical' || si.severity === 'high');

			// Use actual measured values
			return {
				execution_summary: {
					total_tests: testResult.totalTests,
					passed: testResult.passed,
					failed: testResult.failed,
				},
				code_coverage_percentage: testResult.coveragePercentage,
				actionable_recommendations: data.actionable_recommendations ?? [],
				security_issues: securityIssues,
				has_severe_security_issues: hasSevere,
			};
		} catch {
			// Return actual values even if LLM parsing fails
			return {
				execution_summary: {
					total_tests: testResult.totalTests,
					passed: testResult.passed,
					failed: testResult.failed,
				},
				code_coverage_percentage: testResult.coveragePercentage,
				actionable_recommendations: [],
				security_issues: [],
				has_severe_security_issues: false,
			};
		}
	}

	/**
	 * Generates additional tests to improve coverage and address security issues.
	 */
	async generateAdditionalTests(
		codebasePath: string,
		existingTestFile: string,
		currentCoverage: number,
		uncoveredAreas: string,
		securityIssues: readonly ISecurityIssue[],
		token: CancellationToken
	): Promise<ITestImplementationResult> {
		const codebaseUri = URI.file(codebasePath);
		const pythonFiles = await gatherPythonFileUris(codebaseUri, undefined, this.fileSystemService);
		const fileContents = await readFilesContent(pythonFiles, this.fileSystemService);
		const combinedContext = combineFileContents(fileContents);
		const filePaths = extractFilePaths(fileContents);

		// Read existing test code
		let existingTestCode = '';
		try {
			const existingContent = await this.fileSystemService.readFile(URI.file(existingTestFile));
			existingTestCode = new TextDecoder().decode(existingContent);
		} catch {
			// File may not exist
		}

		const endpoint = await this.endpointProvider.getChatEndpoint('copilot-fast');
		const promptRenderer = PromptRenderer.create(
			this.instantiationService,
			endpoint,
			TestCaseImplementationPrompt,
			{
				scenarios: { test_scenarios: [] }, // Empty for improvement mode
				codeContext: combinedContext,
				filePaths,
				existingTestCode,
				uncoveredAreas,
				securityIssues,
			}
		);

		const prompt = await promptRenderer.render();
		const response = await endpoint.makeChatRequest(
			'pythonTestImprovement',
			prompt.messages,
			undefined,
			token,
			ChatLocation.Other
		);

		if (response.type !== ChatFetchResponseType.Success) {
			throw new Error(`Failed to generate additional tests: ${response.reason}`);
		}

		let testCode = this.sanitizeCode(response.value);

		// Validate and fix syntax
		for (let attempt = 0; attempt < 3; attempt++) {
			const { valid, error } = this.validatePythonSyntax(testCode);
			if (valid) {
				break;
			}
			testCode = await this.fixSyntaxError(testCode, error, codebasePath, token);
		}

		// Overwrite existing test file
		await this.fileSystemService.writeFile(URI.file(existingTestFile), new TextEncoder().encode(testCode));

		return {
			testCode,
			filePath: existingTestFile,
			scenarioCount: 0, // Improvement mode
		};
	}

	// ==================== Helper Methods ====================

	/**
	 * Parses JSON response, handling markdown code blocks.
	 */
	private parseJsonResponse<T>(response: string, requiredKey: string): T {
		let jsonStr = response.trim();

		// Remove markdown code blocks if present
		const jsonMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/);
		if (jsonMatch) {
			jsonStr = jsonMatch[1].trim();
		}

		const parsed = JSON.parse(jsonStr);

		if (!(requiredKey in parsed)) {
			throw new Error(`Invalid response structure: missing ${requiredKey}`);
		}

		return parsed as T;
	}

	/**
	 * Removes markdown formatting from code response.
	 */
	private sanitizeCode(response: string): string {
		let code = response.trim();

		// Handle ```python ... ``` blocks
		if (code.startsWith('```')) {
			const firstNewline = code.indexOf('\n');
			if (firstNewline !== -1) {
				code = code.substring(firstNewline + 1);
			}
		}

		// Remove trailing ```
		if (code.endsWith('```')) {
			code = code.slice(0, -3).trimEnd();
		}

		// Fallback regex extraction
		if (code.includes('```')) {
			const match = code.match(/```(?:python)?\s*([\s\S]*?)```/);
			if (match) {
				code = match[1].trim();
			}
		}

		return code.replace(/^`+|`+$/g, '').trim();
	}

	/**
	 * Validates Python syntax by checking balanced brackets.
	 */
	private validatePythonSyntax(code: string): { valid: boolean; error: string } {
		let openParens = 0, openBrackets = 0, openBraces = 0;

		for (const char of code) {
			if (char === '(') { openParens++; }
			else if (char === ')') { openParens--; }
			else if (char === '[') { openBrackets++; }
			else if (char === ']') { openBrackets--; }
			else if (char === '{') { openBraces++; }
			else if (char === '}') { openBraces--; }
		}

		if (openParens !== 0) { return { valid: false, error: 'Unbalanced parentheses' }; }
		if (openBrackets !== 0) { return { valid: false, error: 'Unbalanced brackets' }; }
		if (openBraces !== 0) { return { valid: false, error: 'Unbalanced braces' }; }

		return { valid: true, error: '' };
	}

	/**
	 * Attempts to fix syntax errors via LLM.
	 */
	private async fixSyntaxError(code: string, error: string, codebasePath: string, token: CancellationToken): Promise<string> {
		const codebaseUri = URI.file(codebasePath);
		const pythonFiles = await gatherPythonFileUris(codebaseUri, undefined, this.fileSystemService);
		const fileContents = await readFilesContent(pythonFiles.slice(0, 5), this.fileSystemService);
		const sourceContext = combineFileContents(fileContents);

		const endpoint = await this.endpointProvider.getChatEndpoint('copilot-fast');
		const promptRenderer = PromptRenderer.create(
			this.instantiationService,
			endpoint,
			TestCaseImplementationPrompt,
			{
				scenarios: { test_scenarios: [] },
				codeContext: sourceContext,
				filePaths: fileContents.map(f => f.path),
				existingTestCode: `Error: ${error}\n\nProblematic code:\n${code.substring(0, 2000)}`,
				uncoveredAreas: 'Fix the syntax errors',
			}
		);

		const prompt = await promptRenderer.render();
		const response = await endpoint.makeChatRequest(
			'pythonSyntaxFix',
			prompt.messages,
			undefined,
			token,
			ChatLocation.Other
		);

		if (response.type !== ChatFetchResponseType.Success) {
			return code; // Return original if fix fails
		}

		return this.sanitizeCode(response.value);
	}

	/**
	 * Parses test counts from pytest output.
	 */
	private parseTestCounts(output: string): { total: number; passed: number; failed: number } {
		const passed = parseInt(output.match(/(\d+) passed/)?.[1] ?? '0', 10);
		const failed = parseInt(output.match(/(\d+) failed/)?.[1] ?? '0', 10) +
			parseInt(output.match(/(\d+) error/)?.[1] ?? '0', 10);
		return { total: passed + failed, passed, failed };
	}

	/**
	 * Parses coverage percentage from coverage.json.
	 */
	private async parseCoverageJson(testFilePath: string): Promise<number> {
		try {
			const testDir = URI.file(testFilePath).with({
				path: URI.file(testFilePath).path.replace(/\/[^/]+$/, '')
			});
			const coverageFile = URI.joinPath(testDir, '..', 'coverage.json');
			const content = await this.fileSystemService.readFile(coverageFile);
			const data = JSON.parse(new TextDecoder().decode(content));
			return data.totals?.percent_covered ?? 0;
		} catch {
			return 0;
		}
	}

	/**
	 * Extracts uncovered areas from pytest-cov output.
	 */
	private extractUncoveredAreas(output: string): string {
		const uncovered: string[] = [];
		const pattern = /^(.+\.py)\s+\d+\s+\d+\s+\d+%\s+(.+)$/gm;
		let match;

		while ((match = pattern.exec(output)) !== null) {
			if (match[2].trim()) {
				uncovered.push(`${match[1]}: lines ${match[2]}`);
			}
		}

		return uncovered.length > 0 ? uncovered.join('\n') : 'No specific uncovered areas identified';
	}
}
