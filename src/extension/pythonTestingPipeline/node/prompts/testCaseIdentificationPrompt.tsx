/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { BasePromptElementProps, PromptElement, PromptPiece, PromptSizing, SystemMessage, UserMessage } from '@vscode/prompt-tsx';
import { Tag } from '../../../prompts/node/base/tag';

/**
 * Props for the Test Case Identification Prompt.
 */
export interface TestCaseIdentificationPromptProps extends BasePromptElementProps {
	/** The Python code to analyze */
	readonly codeContent: string;
	/** File paths that were analyzed */
	readonly filePaths: readonly string[];
}

/**
 * Prompt for the Test Case Identification Agent.
 * Analyzes Python code and identifies comprehensive test scenarios.
 */
export class TestCaseIdentificationPrompt extends PromptElement<TestCaseIdentificationPromptProps> {
	override render(_state: void, _sizing: PromptSizing): PromptPiece {
		const { codeContent, filePaths } = this.props;

		return (
			<>
				<SystemMessage priority={1000}>
					### ROLE<br />
					You are a Senior Software Quality Assurance Engineer specializing in Python.<br />
					<br />
					### OBJECTIVE<br />
					Your primary goal is to analyze the given Python codebase and identify a comprehensive list of test scenarios, including critical edge cases, for human approval.<br />
					<br />
					### RULES &amp; CONSTRAINTS<br />
					- Focus exclusively on identifying test scenarios; do not generate test code.<br />
					- Prioritize critical paths, common use cases, and edge cases (e.g., invalid inputs, empty values, concurrency issues).<br />
					- If the code is unclear or incomplete, identify the ambiguity as a test scenario.<br />
					- Ensure each scenario is specific and testable.<br />
					- Consider both positive (happy path) and negative (error handling) test cases.<br />
					- Think about boundary conditions, null/empty inputs, type errors, and exception handling.<br />
					- Be concise and clear in your scenario descriptions.<br />
					<br />
					### OUTPUT FORMAT<br />
					- Provide the response as a single JSON object only.<br />
					- Do NOT include any markdown code blocks or backticks.<br />
					- Do NOT include any explanatory text before or after the JSON.<br />
					- The JSON object should contain one key, "test_scenarios", which holds a list of test case objects.<br />
					- Each test case object must include:<br />
					&nbsp;&nbsp;- "scenario_description": A concise string explaining the test case.<br />
					&nbsp;&nbsp;- "priority": A string with a value of "High", "Medium", or "Low".<br />
					<br />
					### EXAMPLE OUTPUT<br />
					{`{"test_scenarios":[{"scenario_description":"Test user login with valid credentials.","priority":"High"},{"scenario_description":"Test user login with an invalid password.","priority":"High"},{"scenario_description":"Test user login with an empty username field.","priority":"Medium"}]}`}
				</SystemMessage>
				<UserMessage priority={900} flexGrow={1}>
					Please analyze the following Python codebase and identify all test scenarios.<br />
					<br />
					<Tag name="files_analyzed" priority={100}>
						{filePaths.join('\n')}
					</Tag>
					<br />
					<Tag name="code" priority={100}>
						{codeContent}
					</Tag>
					<br />
					Respond with ONLY a JSON object containing the test scenarios. No markdown, no code blocks, no explanation.
				</UserMessage>
			</>
		);
	}
}
