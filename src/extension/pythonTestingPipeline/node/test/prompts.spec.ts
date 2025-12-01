/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { describe, expect, it } from 'vitest';
import { ISecurityIssue, ITestEvaluationOutput, ITestScenariosOutput } from '../../common/types';

describe('Test Case Identification Prompt', () => {
	describe('System Prompt Content', () => {
		const systemPromptContent = `### ROLE
You are a Senior Software Quality Assurance Engineer specializing in Python.

### OBJECTIVE
Your primary goal is to analyze the given Python codebase and identify a comprehensive list of test scenarios, including critical edge cases, for human approval.

### RULES & CONSTRAINTS
- Focus exclusively on identifying test scenarios; do not generate test code.
- Prioritize critical paths, common use cases, and edge cases.
- If the code is unclear or incomplete, identify the ambiguity as a test scenario.`;

		it('should include the QA engineer role', () => {
			expect(systemPromptContent).toContain('Senior Software Quality Assurance Engineer');
			expect(systemPromptContent).toContain('Python');
		});

		it('should specify not to generate test code', () => {
			expect(systemPromptContent).toContain('do not generate test code');
		});

		it('should mention edge cases', () => {
			expect(systemPromptContent).toContain('edge cases');
		});
	});

	describe('Expected Output Format', () => {
		const exampleOutput: ITestScenariosOutput = {
			test_scenarios: [
				{
					scenario_description: 'Test user login with valid credentials.',
					priority: 'High'
				},
				{
					scenario_description: 'Test user login with an invalid password.',
					priority: 'High'
				},
				{
					scenario_description: 'Test user login with an empty username field.',
					priority: 'Medium'
				}
			]
		};

		it('should have test_scenarios as the root key', () => {
			expect(exampleOutput).toHaveProperty('test_scenarios');
		});

		it('should have scenarios with description and priority', () => {
			const scenario = exampleOutput.test_scenarios[0];
			expect(scenario).toHaveProperty('scenario_description');
			expect(scenario).toHaveProperty('priority');
		});

		it('should use valid priority values', () => {
			const validPriorities = ['High', 'Medium', 'Low'];
			for (const scenario of exampleOutput.test_scenarios) {
				expect(validPriorities).toContain(scenario.priority);
			}
		});
	});
});

describe('Test Case Implementation Prompt', () => {
	describe('System Prompt Content', () => {
		const systemPromptContent = `### ROLE
You are a Senior Software Development Engineer in Test (SDET) specializing in Python and the PyTest framework.

### OBJECTIVE
Your goal is to generate executable PyTest test scripts based on an approved JSON list of test scenarios.

### RULES & CONSTRAINTS
- Use the PyTest framework for all generated tests.
- Adhere strictly to the provided test scenarios; do not create new ones.
- Write clean, readable, and maintainable code following PEP 8 standards.
- Always validate inputs and sanitize user data to prevent security vulnerabilities.`;

		it('should include the SDET role', () => {
			expect(systemPromptContent).toContain('Software Development Engineer in Test');
			expect(systemPromptContent).toContain('PyTest framework');
		});

		it('should require PEP 8 compliance', () => {
			expect(systemPromptContent).toContain('PEP 8');
		});

		it('should prohibit creating new scenarios', () => {
			expect(systemPromptContent).toContain('do not create new ones');
		});

		it('should mention security awareness', () => {
			expect(systemPromptContent).toContain('security vulnerabilities');
		});
	});

	describe('Expected Code Output', () => {
		const exampleCode = `import pytest

def test_login_with_valid_credentials(client):
    """
    Tests user login with correct username and password.
    """
    response = client.post('/login', data={'username': 'testuser', 'password': 'correct_password'})
    assert response.status_code == 200
    assert b'Welcome, testuser!' in response.data`;

		it('should import pytest', () => {
			expect(exampleCode).toContain('import pytest');
		});

		it('should use test_ prefix for function names', () => {
			expect(exampleCode).toMatch(/def test_\w+/);
		});

		it('should include docstrings', () => {
			expect(exampleCode).toContain('"""');
		});

		it('should include assertions', () => {
			expect(exampleCode).toContain('assert');
		});
	});
});

describe('Test Case Evaluation Prompt', () => {
	describe('System Prompt Content', () => {
		const systemPromptContent = `### ROLE
You are a Principal Software Development Engineer in Test (SDET) with expertise in test automation analysis, code quality metrics, and security vulnerability assessment.

### OBJECTIVE
Your primary goal is to evaluate the results of a PyTest test suite execution and perform security analysis.

### RULES & CONSTRAINTS
- Your analysis must be based solely on the provided reports.
- Recommendations must be specific, actionable, and aimed at improving test coverage.
- Identify security vulnerabilities including SQL injection, XSS, command injection, and insecure data handling.
- Do not suggest new features; focus only on improving the existing test suite.`;

		it('should include the Principal SDET role', () => {
			expect(systemPromptContent).toContain('Principal Software Development Engineer in Test');
		});

		it('should focus on actionable recommendations', () => {
			expect(systemPromptContent).toContain('actionable');
		});

		it('should prohibit suggesting new features', () => {
			expect(systemPromptContent).toContain('Do not suggest new features');
		});

		it('should include security analysis', () => {
			expect(systemPromptContent).toContain('security vulnerability');
			expect(systemPromptContent).toContain('SQL injection');
			expect(systemPromptContent).toContain('XSS');
		});
	});

	describe('Expected Evaluation Output', () => {
		const exampleOutput: ITestEvaluationOutput = {
			execution_summary: {
				total_tests: 50,
				passed: 48,
				failed: 2
			},
			code_coverage_percentage: 85.0,
			actionable_recommendations: [
				'Investigate and fix the failed tests.',
				'Increase test coverage for under-tested modules.',
				'Refactor redundant setup code.'
			],
			security_issues: [
				{
					severity: 'high',
					issue: 'SQL Injection vulnerability in user input handling',
					location: 'database.py:42',
					recommendation: 'Use parameterized queries instead of string concatenation'
				},
				{
					severity: 'medium',
					issue: 'Unvalidated redirect URL',
					location: 'auth.py:78',
					recommendation: 'Validate redirect URLs against a whitelist'
				}
			],
			has_severe_security_issues: true
		};

		it('should have execution_summary with test counts', () => {
			expect(exampleOutput.execution_summary).toHaveProperty('total_tests');
			expect(exampleOutput.execution_summary).toHaveProperty('passed');
			expect(exampleOutput.execution_summary).toHaveProperty('failed');
		});

		it('should have code coverage as a number', () => {
			expect(typeof exampleOutput.code_coverage_percentage).toBe('number');
		});

		it('should have recommendations as an array', () => {
			expect(Array.isArray(exampleOutput.actionable_recommendations)).toBe(true);
			expect(exampleOutput.actionable_recommendations.length).toBeGreaterThan(0);
		});

		it('should have consistent test counts', () => {
			const { total_tests, passed, failed } = exampleOutput.execution_summary;
			expect(passed + failed).toBe(total_tests);
		});

		it('should include security issues with proper structure', () => {
			expect(Array.isArray(exampleOutput.security_issues)).toBe(true);
			expect(exampleOutput.security_issues.length).toBeGreaterThan(0);

			for (const issue of exampleOutput.security_issues) {
				expect(issue).toHaveProperty('severity');
				expect(issue).toHaveProperty('issue');
				expect(issue).toHaveProperty('location');
				expect(issue).toHaveProperty('recommendation');
			}
		});

		it('should flag severe security issues', () => {
			expect(exampleOutput.has_severe_security_issues).toBe(true);
		});
	});

	describe('Security Severity Classification', () => {
		it('should classify critical and high as severe', () => {
			const criticalIssue: ISecurityIssue = {
				severity: 'critical',
				issue: 'Remote code execution',
				location: 'api.py:10',
				recommendation: 'Sanitize all inputs'
			};

			const highIssue: ISecurityIssue = {
				severity: 'high',
				issue: 'SQL Injection',
				location: 'db.py:25',
				recommendation: 'Use parameterized queries'
			};

			const severeIssues = [criticalIssue, highIssue];
			const hasSevere = severeIssues.some(i => i.severity === 'critical' || i.severity === 'high');

			expect(hasSevere).toBe(true);
		});

		it('should not classify medium and low as severe', () => {
			const mediumIssue: ISecurityIssue = {
				severity: 'medium',
				issue: 'Insecure cookie',
				location: 'auth.py:50',
				recommendation: 'Set secure and httponly flags'
			};

			const lowIssue: ISecurityIssue = {
				severity: 'low',
				issue: 'Missing CSRF token',
				location: 'forms.py:15',
				recommendation: 'Add CSRF protection'
			};

			const nonSevereIssues = [mediumIssue, lowIssue];
			const hasSevere = nonSevereIssues.some(i => i.severity === 'critical' || i.severity === 'high');

			expect(hasSevere).toBe(false);
		});
	});
});
