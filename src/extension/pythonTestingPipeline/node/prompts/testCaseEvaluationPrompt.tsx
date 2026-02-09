/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { BasePromptElementProps, PromptElement, PromptPiece, PromptSizing, SystemMessage, UserMessage } from '@vscode/prompt-tsx';
import { Tag } from '../../../prompts/node/base/tag';
import { IPyTestExecutionResult, ITestScenariosOutput } from '../../common/types';

/**
 * Props for the Test Case Evaluation Prompt.
 */
export interface TestCaseEvaluationPromptProps extends BasePromptElementProps {
	/** The PyTest execution results */
	readonly testResult: IPyTestExecutionResult;
	/** The original approved test scenarios */
	readonly approvedScenarios: ITestScenariosOutput;
	/** Source code for security analysis */
	readonly sourceCode: string;
}

/**
 * Prompt for the Test Case Evaluation Agent.
 * Analyzes test execution results, performs security analysis, and provides actionable recommendations.
 */
export class TestCaseEvaluationPrompt extends PromptElement<TestCaseEvaluationPromptProps> {
	priority = 0;
	insertLineBreakBefore = false;

	override render(_state: void, _sizing: PromptSizing): PromptPiece {
		const { testResult, approvedScenarios, sourceCode } = this.props;

		return (
			<>
				<SystemMessage priority={1000}>
					### ROLE<br />
					You are a Principal Software Development Engineer in Test (SDET) with expertise in test automation analysis, code quality metrics, and security testing.<br />
					<br />
					### OBJECTIVE<br />
					Your primary goal is to:<br />
					1. Evaluate the results of a PyTest test suite execution<br />
					2. Analyze test outcomes and measure code coverage<br />
					3. Perform security analysis on the source code and test code<br />
					4. Provide actionable recommendations to enhance testing quality and security<br />
					<br />
					### RULES &amp; CONSTRAINTS<br />
					- Your analysis must be based solely on the provided reports.<br />
					- Recommendations must be specific, actionable, and aimed at improving test coverage, robustness, AND security.<br />
					- Do not suggest new features; focus only on improving the existing test suite.<br />
					- Parse the PyTest output carefully to extract pass/fail counts.<br />
					- If coverage data is available, use it to identify under-tested areas.<br />
					- Consider the priority of the original test scenarios when making recommendations.<br />
					- Security issues should be classified by severity: "critical", "high", "medium", "low".<br />
					- Critical/High severity issues MUST be addressed before the pipeline can complete.<br />
					- Be concise and clear in your analysis.<br />
					<br />
					### SECURITY ANALYSIS FOCUS AREAS<br />
					- SQL Injection vulnerabilities<br />
					- Cross-Site Scripting (XSS)<br />
					- Command Injection<br />
					- Path Traversal attacks<br />
					- Insecure deserialization<br />
					- Hardcoded secrets/credentials<br />
					- Insecure cryptographic practices<br />
					- Missing input validation<br />
					- Improper error handling that leaks sensitive info<br />
					- Insecure dependencies<br />
					<br />
					### OUTPUT FORMAT<br />
					- Provide the response as a single JSON object only.<br />
					- Do NOT include any markdown code blocks or backticks.<br />
					- Do NOT include any explanatory text before or after the JSON.<br />
					- The JSON object must contain these keys:<br />
					&nbsp;&nbsp;- "execution_summary": An object containing integer values for "total_tests", "passed", and "failed".<br />
					&nbsp;&nbsp;- "code_coverage_percentage": A float value representing the total coverage (e.g., 92.5).<br />
					&nbsp;&nbsp;- "security_issues": A list of objects with "severity" (critical/high/medium/low), "issue", "location", and "recommendation".<br />
					&nbsp;&nbsp;- "has_severe_security_issues": Boolean - true if any critical or high severity issues exist.<br />
					&nbsp;&nbsp;- "actionable_recommendations": A list of concise strings for improving coverage and fixing issues.<br />
					<br />
					### EXAMPLE OUTPUT<br />
					{`{"execution_summary":{"total_tests":50,"passed":48,"failed":2},"code_coverage_percentage":85.0,"security_issues":[{"severity":"high","issue":"SQL Injection vulnerability","location":"database.py:45","recommendation":"Use parameterized queries"}],"has_severe_security_issues":true,"actionable_recommendations":["Fix SQL injection in database.py","Increase coverage for user_utils.py"]}`}
				</SystemMessage>
				<UserMessage priority={900} flexGrow={1}>
					Please analyze the following PyTest execution results and perform security analysis.<br />
					<br />
					<Tag name="test_results" priority={200}>
						Test Execution Results:<br />
						- Total tests: {testResult.totalTests}<br />
						- Passed: {testResult.passed}<br />
						- Failed: {testResult.failed}<br />
						- Coverage: {testResult.coveragePercentage.toFixed(1)}%<br />
						- Exit code: {testResult.exitCode}
					</Tag>
					<br />
					<Tag name="pytest_output" priority={180}>
						{testResult.stdout}<br />
						{testResult.stderr}
					</Tag>
					<br />
					<Tag name="approved_scenarios" priority={150}>
						The tests were generated for these scenarios:<br />
						{JSON.stringify(approvedScenarios, null, 2)}
					</Tag>
					<br />
					<Tag name="source_code" priority={100}>
						Source code for security analysis:<br />
						{sourceCode}
					</Tag>
					<br />
					<br />
					Respond with ONLY a JSON object containing the evaluation. No markdown, no code blocks, no explanation.
				</UserMessage>
			</>
		);
	}
}
