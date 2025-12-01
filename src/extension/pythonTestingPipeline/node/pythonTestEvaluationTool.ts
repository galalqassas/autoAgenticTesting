/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as l10n from '@vscode/l10n';
import type * as vscode from 'vscode';
import { IFileSystemService } from '../../../platform/filesystem/common/fileSystemService';
import { IPromptPathRepresentationService } from '../../../platform/prompts/common/promptPathRepresentationService';
import { ITelemetryService } from '../../../platform/telemetry/common/telemetry';
import { CancellationToken } from '../../../util/vs/base/common/cancellation';
import { IInstantiationService } from '../../../util/vs/platform/instantiation/common/instantiation';
import { LanguageModelTextPart, LanguageModelToolResult, MarkdownString } from '../../../vscodeTypes';
import { IBuildPromptContext } from '../../prompt/common/intents';
import { ToolName } from '../../tools/common/toolNames';
import { ICopilotTool, ToolRegistry } from '../../tools/common/toolsRegistry';
import { formatUriForFileWidget } from '../../tools/common/toolUtils';
import { resolveToolInputPath } from '../../tools/node/toolUtils';
import { IPyTestExecutionResult, ISecurityIssue, ITestEvaluationOutput } from '../common/types';
import { PythonTestingPipelineService } from './pythonTestingPipelineService';
import { gatherPythonFiles, parseScenarios, sendTestEvaluationTelemetry } from './toolUtils';

/**
 * Input parameters for the Python Test Evaluation Tool.
 */
export interface IPythonTestEvaluationParams {
	/** Path to the test file that was executed */
	readonly testFilePath: string;
	/** Path to the Python codebase for security analysis */
	readonly codebasePath: string;
	/** The approved scenarios JSON string */
	readonly approvedScenarios: string;
}

/**
 * Tool that evaluates PyTest execution results and performs security analysis.
 * This is the third step in the Python Testing Pipeline.
 */
export class PythonTestEvaluationTool implements ICopilotTool<IPythonTestEvaluationParams> {
	public static readonly toolName = 'evaluatePythonTests' as ToolName;

	constructor(
		@IPromptPathRepresentationService private readonly promptPathRepresentationService: IPromptPathRepresentationService,
		@IInstantiationService private readonly instantiationService: IInstantiationService,
		@ITelemetryService private readonly telemetryService: ITelemetryService,
		@IFileSystemService private readonly fileSystemService: IFileSystemService,
	) { }

	async invoke(
		options: vscode.LanguageModelToolInvocationOptions<IPythonTestEvaluationParams>,
		token: vscode.CancellationToken
	): Promise<vscode.LanguageModelToolResult> {
		const { testFilePath, codebasePath, approvedScenarios } = options.input;

		if (!testFilePath || !codebasePath || !approvedScenarios) {
			throw new Error('testFilePath, codebasePath, and approvedScenarios are required');
		}

		const scenarios = parseScenarios(approvedScenarios);
		const resolvedTestPath = this.promptPathRepresentationService.resolveFilePath(testFilePath);
		const resolvedCodebasePath = this.promptPathRepresentationService.resolveFilePath(codebasePath);

		if (!resolvedTestPath || !resolvedCodebasePath) {
			throw new Error('Invalid path provided');
		}

		const pipelineService = this.instantiationService.createInstance(PythonTestingPipelineService);

		// Run the tests
		const testResult = await pipelineService.runTests(
			resolvedTestPath.fsPath,
			resolvedCodebasePath.fsPath,
			token as CancellationToken
		);

		// Read source files for security analysis
		const sourceFiles = await gatherPythonFiles(resolvedCodebasePath, this.fileSystemService);

		// Evaluate results
		const evaluation = await pipelineService.evaluateResults(
			testResult,
			scenarios,
			sourceFiles,
			token as CancellationToken
		);

		const response = this.formatResponse(testResult, evaluation);
		sendTestEvaluationTelemetry(
			this.telemetryService,
			options.chatRequestId,
			evaluation.execution_summary.total_tests,
			evaluation.execution_summary.passed,
			evaluation.code_coverage_percentage,
			evaluation.security_issues.length
		);

		return new LanguageModelToolResult([new LanguageModelTextPart(response)]);
	}

	async resolveInput(
		input: IPythonTestEvaluationParams,
		_promptContext: IBuildPromptContext
	): Promise<IPythonTestEvaluationParams> {
		return input;
	}

	async prepareInvocation(
		options: vscode.LanguageModelToolInvocationPrepareOptions<IPythonTestEvaluationParams>,
		_token: vscode.CancellationToken
	): Promise<vscode.PreparedToolInvocation> {
		const uri = resolveToolInputPath(options.input.testFilePath, this.promptPathRepresentationService);
		return {
			invocationMessage: new MarkdownString(l10n.t`Running and evaluating tests at ${formatUriForFileWidget(uri)}`),
			pastTenseMessage: new MarkdownString(l10n.t`Ran and evaluated tests at ${formatUriForFileWidget(uri)}`)
		};
	}

	private formatResponse(testResult: IPyTestExecutionResult, evaluation: ITestEvaluationOutput): string {
		const { execution_summary, code_coverage_percentage, actionable_recommendations, security_issues, has_severe_security_issues } = evaluation;
		const passRate = execution_summary.total_tests > 0
			? ((execution_summary.passed / execution_summary.total_tests) * 100).toFixed(1)
			: '0';

		const statusEmoji = execution_summary.failed === 0 && !has_severe_security_issues ? '✅' : '⚠️';
		const securityEmoji = has_severe_security_issues ? '🚨' : '🔒';

		const recommendationsList = actionable_recommendations.length > 0
			? actionable_recommendations.map((r, i) => `${i + 1}. ${r}`).join('\n')
			: '_No specific recommendations._';

		const securitySection = this.formatSecuritySection(security_issues, has_severe_security_issues);

		return `## Test Evaluation Report ${statusEmoji}

### Execution Summary

| Metric | Value |
|--------|-------|
| Total Tests | ${execution_summary.total_tests} |
| Passed | ${execution_summary.passed} |
| Failed | ${execution_summary.failed} |
| Pass Rate | ${passRate}% |
| Code Coverage | ${code_coverage_percentage.toFixed(1)}% |

### Security Analysis ${securityEmoji}

${securitySection}

### Recommendations

${recommendationsList}

### Test Output

<details>
<summary>Click to expand test output</summary>

\`\`\`
${testResult.stdout.slice(0, 3000)}${testResult.stdout.length > 3000 ? '\n... (truncated)' : ''}
\`\`\`

</details>

${testResult.stderr ? `### Errors\n\n\`\`\`\n${testResult.stderr.slice(0, 1000)}\n\`\`\`` : ''}`;
	}

	private formatSecuritySection(issues: readonly ISecurityIssue[], hasSevere: boolean): string {
		if (issues.length === 0) {
			return '_No security issues detected._';
		}

		const criticalIssues = issues.filter(i => i.severity === 'critical');
		const highIssues = issues.filter(i => i.severity === 'high');
		const mediumIssues = issues.filter(i => i.severity === 'medium');
		const lowIssues = issues.filter(i => i.severity === 'low');

		let output = `Found **${issues.length}** security issue(s):\n`;
		output += `- 🔴 Critical: ${criticalIssues.length}\n`;
		output += `- 🟠 High: ${highIssues.length}\n`;
		output += `- 🟡 Medium: ${mediumIssues.length}\n`;
		output += `- 🟢 Low: ${lowIssues.length}\n\n`;

		if (hasSevere) {
			output += `> ⚠️ **Action Required:** Critical or high severity issues must be addressed.\n\n`;
		}

		// Show top issues
		const topIssues = [...criticalIssues, ...highIssues].slice(0, 5);
		if (topIssues.length > 0) {
			output += `#### Top Issues\n\n`;
			for (const issue of topIssues) {
				const severityIcon = issue.severity === 'critical' ? '🔴' : '🟠';
				output += `${severityIcon} **${issue.issue}**\n`;
				output += `   - Location: \`${issue.location}\`\n`;
				output += `   - Fix: ${issue.recommendation}\n\n`;
			}
		}

		return output;
	}
}

ToolRegistry.registerTool(PythonTestEvaluationTool);
