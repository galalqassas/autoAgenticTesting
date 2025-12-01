/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as l10n from '@vscode/l10n';
import type * as vscode from 'vscode';
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
import { ITestImplementationResult } from '../common/types';
import { PythonTestingPipelineService } from './pythonTestingPipelineService';
import { parseScenarios, sendTestImplementationTelemetry } from './toolUtils';

/**
 * Input parameters for the Python Test Implementation Tool.
 */
export interface IPythonTestImplementationParams {
	/** The approved test scenarios as JSON string */
	readonly approvedScenarios: string;
	/** Path to the Python codebase for context */
	readonly codebasePath: string;
	/** Optional: output directory for the generated test file */
	readonly outputDir?: string;
}

/**
 * Tool that generates PyTest implementation from approved test scenarios.
 * This is the second step in the Python Testing Pipeline.
 */
export class PythonTestImplementationTool implements ICopilotTool<IPythonTestImplementationParams> {
	public static readonly toolName = 'implementPythonTests' as ToolName;

	constructor(
		@IPromptPathRepresentationService private readonly promptPathRepresentationService: IPromptPathRepresentationService,
		@IInstantiationService private readonly instantiationService: IInstantiationService,
		@ITelemetryService private readonly telemetryService: ITelemetryService,
	) { }

	async invoke(
		options: vscode.LanguageModelToolInvocationOptions<IPythonTestImplementationParams>,
		token: vscode.CancellationToken
	): Promise<vscode.LanguageModelToolResult> {
		const { approvedScenarios, codebasePath, outputDir } = options.input;

		if (!approvedScenarios || !codebasePath) {
			throw new Error('approvedScenarios and codebasePath are required');
		}

		const scenarios = parseScenarios(approvedScenarios);
		const resolvedPath = this.promptPathRepresentationService.resolveFilePath(codebasePath);
		if (!resolvedPath) {
			throw new Error(`Invalid path: ${codebasePath}`);
		}

		const pipelineService = this.instantiationService.createInstance(PythonTestingPipelineService);
		const result = await pipelineService.generateTestCode(
			scenarios,
			resolvedPath.fsPath,
			outputDir ?? resolvedPath.fsPath,
			token as CancellationToken
		);

		const response = this.formatResponse(result);
		sendTestImplementationTelemetry(this.telemetryService, options.chatRequestId, result.scenarioCount);

		return new LanguageModelToolResult([new LanguageModelTextPart(response)]);
	}

	async resolveInput(
		input: IPythonTestImplementationParams,
		_promptContext: IBuildPromptContext
	): Promise<IPythonTestImplementationParams> {
		return input;
	}

	async prepareInvocation(
		options: vscode.LanguageModelToolInvocationPrepareOptions<IPythonTestImplementationParams>,
		_token: vscode.CancellationToken
	): Promise<vscode.PreparedToolInvocation> {
		const uri = resolveToolInputPath(options.input.codebasePath, this.promptPathRepresentationService);
		return {
			invocationMessage: new MarkdownString(l10n.t`Generating PyTest test file for ${formatUriForFileWidget(uri)}`),
			pastTenseMessage: new MarkdownString(l10n.t`Generated PyTest test file for ${formatUriForFileWidget(uri)}`)
		};
	}

	private formatResponse(result: ITestImplementationResult): string {
		return `## Generated PyTest Test File

Created test file: \`${result.filePath}\`

Implemented **${result.scenarioCount}** test scenarios.

### Generated Code

\`\`\`python
${result.testCode}
\`\`\`

### Running the Tests

Run with coverage:
\`\`\`bash
pytest ${result.filePath} --cov --cov-report=term-missing -v
\`\`\`

Run without coverage:
\`\`\`bash
pytest ${result.filePath} -v
\`\`\`

### Next Steps

Use the \`evaluatePythonTests\` tool with the test output to get evaluation and recommendations.`;
	}
}

ToolRegistry.registerTool(PythonTestImplementationTool);
