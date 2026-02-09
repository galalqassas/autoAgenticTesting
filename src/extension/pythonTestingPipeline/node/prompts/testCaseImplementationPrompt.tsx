/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { BasePromptElementProps, PromptElement, PromptPiece, PromptSizing, SystemMessage, UserMessage } from '@vscode/prompt-tsx';
import { Tag } from '../../../prompts/node/base/tag';
import { ISecurityIssue, ITestScenariosOutput } from '../../common/types';

/**
 * Props for the Test Case Implementation Prompt.
 */
export interface TestCaseImplementationPromptProps extends BasePromptElementProps {
	/** The approved test scenarios */
	readonly scenarios: ITestScenariosOutput;
	/** The source code context for reference */
	readonly codeContext: string;
	/** The file paths of the source code */
	readonly filePaths: readonly string[];
	/** Optional: existing test code to improve */
	readonly existingTestCode?: string;
	/** Optional: uncovered code areas to target */
	readonly uncoveredAreas?: string;
	/** Optional: security issues to address */
	readonly securityIssues?: readonly ISecurityIssue[];
}

/**
 * Prompt for the Test Case Implementation Agent.
 * Generates PyTest test scripts from approved test scenarios.
 */
export class TestCaseImplementationPrompt extends PromptElement<TestCaseImplementationPromptProps> {
	priority = 0;
	insertLineBreakBefore = false;

	override render(_state: void, _sizing: PromptSizing): PromptPiece {
		const { scenarios, codeContext, filePaths, existingTestCode, uncoveredAreas, securityIssues } = this.props;
		const isImprovement = !!existingTestCode;

		return (
			<>
				<SystemMessage priority={1000}>
					### ROLE<br />
					You are a Senior Software Development Engineer in Test (SDET) specializing in Python and the PyTest framework.<br />
					<br />
					### OBJECTIVE<br />
					{isImprovement
						? <>Your goal is to improve an existing PyTest test file to increase code coverage and address security issues.<br /></>
						: <>Your goal is to generate executable PyTest test scripts based on an approved JSON list of test scenarios.<br /></>
					}
					<br />
					### CRITICAL RULES<br />
					- Return ONLY raw Python code - NO markdown formatting, NO code fences (``` or ```python).<br />
					- The output must be valid Python that can be saved directly to a .py file.<br />
					- Use the PyTest framework for all generated tests.<br />
					- Adhere strictly to the provided test scenarios; do not create new ones.<br />
					- Write clean, readable, and maintainable code following PEP 8 standards.<br />
					- Ensure each test function is self-contained and corresponds directly to a single test scenario.<br />
					- Use meaningful test function names that reflect the scenario (e.g., test_login_with_invalid_password).<br />
					- Include appropriate imports for pytest and any modules being tested.<br />
					- Use pytest fixtures where appropriate for setup and teardown.<br />
					- Add docstrings to each test function explaining what it tests.<br />
					- Handle both positive and negative test cases appropriately with assertions.<br />
					- Use pytest.raises() for testing exceptions.<br />
					- Use parametrized tests when testing similar scenarios with different inputs.<br />
					- Be concise and clear in your code and comments.<br />
					<br />
					### OUTPUT FORMAT<br />
					- Provide the response as a single, complete Python script.<br />
					- Do NOT wrap the code in markdown code blocks or backticks.<br />
					- The script should be ready for execution without any modifications.<br />
					- Start directly with the Python imports.<br />
					- Function names should clearly reflect the scenario they are testing.<br />
					<br />
					### IMPORTANT<br />
					- Analyze the source code context to understand the module structure and function signatures.<br />
					- Import the actual modules and functions being tested based on the source code.<br />
					- Create mock objects or fixtures as needed to isolate tests.<br />
				</SystemMessage>
				<UserMessage priority={900} flexGrow={1}>
					{isImprovement ? (
						<>
							The current test suite needs improvements to increase coverage and address issues.<br />
							<br />
							<Tag name="existing_tests" priority={200}>
								{existingTestCode}
							</Tag>
							<br />
							{uncoveredAreas && (
								<>
									<br />
									<Tag name="uncovered_areas" priority={180}>
										{uncoveredAreas}
									</Tag>
									<br />
								</>
							)}
							{securityIssues && securityIssues.length > 0 && (
								<>
									<br />
									<Tag name="security_issues" priority={190}>
										The following security vulnerabilities need test coverage:<br />
										{securityIssues.map(si => (
											<>[{si.severity.toUpperCase()}] {si.issue} at {si.location}<br /></>
										))}
									</Tag>
									<br />
								</>
							)}
						</>
					) : (
						<>
							Generate PyTest test code for the following approved test scenarios:<br />
							<br />
							<Tag name="approved_scenarios" priority={200}>
								{JSON.stringify(scenarios, null, 2)}
							</Tag>
							<br />
						</>
					)}
					<br />
					Here is the source code context for reference (use this to understand what to import and test):<br />
					<br />
					<Tag name="source_files" priority={150}>
						{filePaths.join('\n')}
					</Tag>
					<br />
					<Tag name="source_code" priority={100}>
						{codeContext}
					</Tag>
					<br />
					<br />
					Generate the complete PyTest test file. Output ONLY the Python code, no markdown formatting.
				</UserMessage>
			</>
		);
	}
}
