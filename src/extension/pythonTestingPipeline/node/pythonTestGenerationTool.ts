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
import { ITestScenariosOutput } from '../common/types';
import { PythonTestingPipelineService } from './pythonTestingPipelineService';
import { sendTestGenerationTelemetry } from './toolUtils';

/**
 * Input parameters for the Python Test Generation Tool.
 */
export interface IPythonTestGenerationParams {
	/** Path to the Python codebase or file to analyze */
	readonly codebasePath: string;
	/** Optional: specific Python files to analyze */
	readonly targetFiles?: readonly string[];
}

/**
 * Tool that identifies test scenarios from Python code.
 * This is the first step in the Python Testing Pipeline.
 */
export class PythonTestGenerationTool implements ICopilotTool<IPythonTestGenerationParams> {
	public static readonly toolName = 'generatePythonTests' as ToolName;

	constructor(
		@IPromptPathRepresentationService private readonly promptPathRepresentationService: IPromptPathRepresentationService,
		@IInstantiationService private readonly instantiationService: IInstantiationService,
		@ITelemetryService private readonly telemetryService: ITelemetryService,
	) { }

	async invoke(
		options: vscode.LanguageModelToolInvocationOptions<IPythonTestGenerationParams>,
		token: vscode.CancellationToken
	): Promise<vscode.LanguageModelToolResult> {
		const { codebasePath, targetFiles } = options.input;

		if (!codebasePath) {
			throw new Error('codebasePath is required');
		}

		const resolvedPath = this.promptPathRepresentationService.resolveFilePath(codebasePath);
		if (!resolvedPath) {
			throw new Error(`Invalid path: ${codebasePath}`);
		}

		const pipelineService = this.instantiationService.createInstance(PythonTestingPipelineService);
		const scenarios = await pipelineService.identifyTestScenarios(
			resolvedPath.fsPath,
			targetFiles,
			token as CancellationToken
		);

		const response = this.formatResponse(scenarios);
		sendTestGenerationTelemetry(this.telemetryService, options.chatRequestId, scenarios.test_scenarios.length);

		return new LanguageModelToolResult([new LanguageModelTextPart(response)]);
	}

	async resolveInput(
		input: IPythonTestGenerationParams,
		_promptContext: IBuildPromptContext
	): Promise<IPythonTestGenerationParams> {
		return input;
	}

	async prepareInvocation(
		options: vscode.LanguageModelToolInvocationPrepareOptions<IPythonTestGenerationParams>,
		_token: vscode.CancellationToken
	): Promise<vscode.PreparedToolInvocation> {
		const uri = resolveToolInputPath(options.input.codebasePath, this.promptPathRepresentationService);
		return {
			invocationMessage: new MarkdownString(l10n.t`Analyzing Python code at ${formatUriForFileWidget(uri)}`),
			pastTenseMessage: new MarkdownString(l10n.t`Analyzed Python code at ${formatUriForFileWidget(uri)}`)
		};
	}

	private formatResponse(scenarios: ITestScenariosOutput): string {
		const scenariosList = scenarios.test_scenarios
			.map((s, i) => `${i + 1}. **[${s.priority}]** ${s.scenario_description}`)
			.join('\n');

		const highPriority = scenarios.test_scenarios.filter(s => s.priority === 'High').length;
		const mediumPriority = scenarios.test_scenarios.filter(s => s.priority === 'Medium').length;
		const lowPriority = scenarios.test_scenarios.filter(s => s.priority === 'Low').length;

		return `## Identified Test Scenarios

Found **${scenarios.test_scenarios.length}** test scenarios:
- High Priority: ${highPriority}
- Medium Priority: ${mediumPriority}
- Low Priority: ${lowPriority}

### Scenarios

${scenariosList}

### Next Steps

Use the \`implementPythonTests\` tool with the scenarios below to generate PyTest code.

\`\`\`json
${JSON.stringify(scenarios, null, 2)}
\`\`\``;
	}
}

ToolRegistry.registerTool(PythonTestGenerationTool);
