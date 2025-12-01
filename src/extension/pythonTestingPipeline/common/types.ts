/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

/**
 * Priority level for test scenarios.
 */
export type TestPriority = 'High' | 'Medium' | 'Low';

/**
 * Security issue severity levels.
 */
export type SecuritySeverity = 'critical' | 'high' | 'medium' | 'low';

/**
 * Represents a single test scenario identified by the Test Case Identification Agent.
 */
export interface ITestScenario {
	/** A concise description of what this test case should verify */
	readonly scenario_description: string;
	/** Priority level of this test case */
	readonly priority: TestPriority;
}

/**
 * The output format from the Test Case Identification Agent.
 */
export interface ITestScenariosOutput {
	readonly test_scenarios: readonly ITestScenario[];
}

/**
 * Execution summary from running the test suite.
 */
export interface IExecutionSummary {
	readonly total_tests: number;
	readonly passed: number;
	readonly failed: number;
}

/**
 * Represents a security vulnerability found during code analysis.
 */
export interface ISecurityIssue {
	/** Severity level of the security issue */
	readonly severity: SecuritySeverity;
	/** Description of the security issue */
	readonly issue: string;
	/** Location in the code where the issue was found */
	readonly location: string;
	/** Recommended fix for the issue */
	readonly recommendation: string;
}

/**
 * The output format from the Test Case Evaluation Agent.
 */
export interface ITestEvaluationOutput {
	readonly execution_summary: IExecutionSummary;
	readonly code_coverage_percentage: number;
	readonly actionable_recommendations: readonly string[];
	/** Security issues found during analysis */
	readonly security_issues: readonly ISecurityIssue[];
	/** True if any critical or high severity security issues exist */
	readonly has_severe_security_issues: boolean;
}

/**
 * The status of the pipeline at any given point.
 */
export type PipelineStatus =
	| 'pending_identification'
	| 'awaiting_approval'
	| 'generating_tests'
	| 'running_tests'
	| 'evaluating_results'
	| 'improving_coverage'
	| 'completed'
	| 'failed';

/**
 * Represents the state of the entire testing pipeline.
 */
export interface IPipelineState {
	status: PipelineStatus;
	identifiedScenarios?: ITestScenariosOutput;
	approvedScenarios?: ITestScenariosOutput;
	generatedTestCode?: string;
	testFilePath?: string;
	evaluationResult?: ITestEvaluationOutput;
	iteration?: number;
	error?: string;
}

/**
 * Options for running the Python testing pipeline.
 */
export interface IPythonTestingPipelineOptions {
	/** The root directory of the Python codebase to analyze */
	readonly codebasePath: string;
	/** Optional: specific files to analyze (if not provided, analyzes all Python files) */
	readonly targetFiles?: readonly string[];
	/** Optional: output directory for generated tests */
	readonly testOutputDir?: string;
	/** Optional: whether to run tests automatically after generation. Defaults to true. */
	readonly autoRunTests?: boolean;
	/** Optional: collect coverage data when running tests. Defaults to true. */
	readonly collectCoverage?: boolean;
	/** Optional: target coverage percentage (default: 90) */
	readonly targetCoverage?: number;
	/** Optional: maximum iterations for coverage improvement (default: 20) */
	readonly maxIterations?: number;
}

/**
 * Result from the Test Case Implementation Agent.
 */
export interface ITestImplementationResult {
	readonly testCode: string;
	readonly filePath: string;
	readonly scenarioCount: number;
}

/**
 * Result from running the PyTest suite.
 */
export interface IPyTestExecutionResult {
	readonly exitCode: number;
	readonly stdout: string;
	readonly stderr: string;
	readonly totalTests: number;
	readonly passed: number;
	readonly failed: number;
	readonly coveragePercentage: number;
}

/**
 * File content with its path.
 */
export interface IFileContent {
	readonly path: string;
	readonly content: string;
}

/**
 * Prompt history entry for tracking LLM interactions.
 */
export interface IPromptHistoryEntry {
	readonly timestamp: string;
	readonly agent: string;
	readonly systemPrompt: string;
	readonly userPrompt: string;
	readonly response: string;
}
