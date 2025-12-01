/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { createServiceIdentifier } from '../../../util/common/services';
import { CancellationToken } from '../../../util/vs/base/common/cancellation';
import {
	IFileContent,
	IPipelineState,
	IPyTestExecutionResult,
	IPythonTestingPipelineOptions,
	ISecurityIssue,
	ITestEvaluationOutput,
	ITestImplementationResult,
	ITestScenariosOutput,
} from './types';

/**
 * Service identifier for the Python Testing Pipeline Service.
 */
export const IPythonTestingPipelineService = createServiceIdentifier<IPythonTestingPipelineService>('IPythonTestingPipelineService');

/**
 * Main service interface for the Python automated testing pipeline.
 * Orchestrates the three agents: Identification, Implementation, and Evaluation.
 */
export interface IPythonTestingPipelineService {
	_serviceBrand: undefined;

	/**
	 * Runs the complete testing pipeline with coverage improvement loop.
	 * Continues until target coverage is reached or max iterations exceeded.
	 * @param options Configuration options for the pipeline
	 * @param token Cancellation token
	 * @returns The final pipeline state
	 */
	runPipeline(options: IPythonTestingPipelineOptions, token: CancellationToken): Promise<IPipelineState>;

	/**
	 * Agent 1: Identifies test scenarios from the codebase.
	 * @param codebasePath Path to the Python codebase
	 * @param targetFiles Optional specific files to analyze
	 * @param token Cancellation token
	 * @returns Identified test scenarios as JSON
	 */
	identifyTestScenarios(codebasePath: string, targetFiles: readonly string[] | undefined, token: CancellationToken): Promise<ITestScenariosOutput>;

	/**
	 * Requests human approval for identified scenarios.
	 * @param scenarios The identified test scenarios
	 * @param token Cancellation token
	 * @returns Approved scenarios (may be modified by user)
	 */
	requestApproval(scenarios: ITestScenariosOutput, token: CancellationToken): Promise<ITestScenariosOutput>;

	/**
	 * Agent 2: Generates PyTest test code from approved scenarios.
	 * Includes syntax validation and automatic fixing.
	 * @param scenarios Approved test scenarios
	 * @param codebasePath Path to the codebase for context
	 * @param outputDir Directory to write the test file
	 * @param token Cancellation token
	 * @returns Generated test implementation
	 */
	generateTestCode(scenarios: ITestScenariosOutput, codebasePath: string, outputDir: string, token: CancellationToken): Promise<ITestImplementationResult>;

	/**
	 * Runs the generated PyTest suite with coverage measurement.
	 * @param testFilePath Path to the generated test file
	 * @param codebasePath Path to measure coverage against
	 * @param token Cancellation token
	 * @returns Test execution results with coverage data
	 */
	runTests(testFilePath: string, codebasePath: string, token: CancellationToken): Promise<IPyTestExecutionResult>;

	/**
	 * Agent 3: Evaluates test results, coverage, and performs security analysis.
	 * @param testResult Test execution results
	 * @param scenarios The approved test scenarios
	 * @param sourceCode Source code for security analysis
	 * @param token Cancellation token
	 * @returns Evaluation results with recommendations and security issues
	 */
	evaluateResults(testResult: IPyTestExecutionResult, scenarios: ITestScenariosOutput, sourceCode: readonly IFileContent[], token: CancellationToken): Promise<ITestEvaluationOutput>;

	/**
	 * Generates additional tests to improve coverage and address security issues.
	 * @param codebasePath Path to the codebase
	 * @param existingTestFile Path to the current test file
	 * @param currentCoverage Current coverage percentage
	 * @param uncoveredAreas Description of uncovered code areas
	 * @param securityIssues Security issues to address
	 * @param token Cancellation token
	 * @returns Updated test implementation
	 */
	generateAdditionalTests(
		codebasePath: string,
		existingTestFile: string,
		currentCoverage: number,
		uncoveredAreas: string,
		securityIssues: readonly ISecurityIssue[],
		token: CancellationToken
	): Promise<ITestImplementationResult>;
}
