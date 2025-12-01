/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { describe, expect, it } from 'vitest';
import {
	IPipelineState,
	ISecurityIssue,
	ITestEvaluationOutput,
	ITestScenario,
	ITestScenariosOutput,
	PipelineStatus,
	SecuritySeverity,
} from '../../common/types';

describe('Python Testing Pipeline Types', () => {
	describe('ITestScenario', () => {
		it('should accept valid priority values', () => {
			const highPriority: ITestScenario = {
				scenario_description: 'Test login with valid credentials',
				priority: 'High'
			};

			const mediumPriority: ITestScenario = {
				scenario_description: 'Test login with special characters',
				priority: 'Medium'
			};

			const lowPriority: ITestScenario = {
				scenario_description: 'Test login page styling',
				priority: 'Low'
			};

			expect(highPriority.priority).toBe('High');
			expect(mediumPriority.priority).toBe('Medium');
			expect(lowPriority.priority).toBe('Low');
		});

		it('should have required fields', () => {
			const scenario: ITestScenario = {
				scenario_description: 'Test user registration flow',
				priority: 'High'
			};

			expect(scenario).toHaveProperty('scenario_description');
			expect(scenario).toHaveProperty('priority');
		});
	});

	describe('ITestScenariosOutput', () => {
		it('should contain an array of test scenarios', () => {
			const output: ITestScenariosOutput = {
				test_scenarios: [
					{ scenario_description: 'Test 1', priority: 'High' },
					{ scenario_description: 'Test 2', priority: 'Medium' },
					{ scenario_description: 'Test 3', priority: 'Low' }
				]
			};

			expect(output.test_scenarios).toHaveLength(3);
			expect(output.test_scenarios[0].priority).toBe('High');
		});

		it('should handle empty scenarios array', () => {
			const output: ITestScenariosOutput = {
				test_scenarios: []
			};

			expect(output.test_scenarios).toHaveLength(0);
		});
	});

	describe('ISecurityIssue', () => {
		it('should accept valid severity levels', () => {
			const severities: SecuritySeverity[] = ['critical', 'high', 'medium', 'low'];

			for (const severity of severities) {
				const issue: ISecurityIssue = {
					severity,
					issue: 'SQL Injection vulnerability',
					location: 'app.py:42',
					recommendation: 'Use parameterized queries'
				};

				expect(issue.severity).toBe(severity);
			}
		});

		it('should have all required fields', () => {
			const issue: ISecurityIssue = {
				severity: 'critical',
				issue: 'Command injection in subprocess call',
				location: 'utils.py:15',
				recommendation: 'Use subprocess with shell=False'
			};

			expect(issue).toHaveProperty('severity');
			expect(issue).toHaveProperty('issue');
			expect(issue).toHaveProperty('location');
			expect(issue).toHaveProperty('recommendation');
		});
	});

	describe('ITestEvaluationOutput', () => {
		it('should contain all required fields including security', () => {
			const evaluation: ITestEvaluationOutput = {
				execution_summary: {
					total_tests: 10,
					passed: 8,
					failed: 2
				},
				code_coverage_percentage: 75.5,
				actionable_recommendations: [
					'Fix the failing tests in module X',
					'Add more edge case tests'
				],
				security_issues: [
					{
						severity: 'high',
						issue: 'SQL Injection',
						location: 'db.py:25',
						recommendation: 'Use parameterized queries'
					}
				],
				has_severe_security_issues: true
			};

			expect(evaluation.execution_summary.total_tests).toBe(10);
			expect(evaluation.execution_summary.passed).toBe(8);
			expect(evaluation.execution_summary.failed).toBe(2);
			expect(evaluation.code_coverage_percentage).toBe(75.5);
			expect(evaluation.actionable_recommendations).toHaveLength(2);
			expect(evaluation.security_issues).toHaveLength(1);
			expect(evaluation.has_severe_security_issues).toBe(true);
		});

		it('should handle zero coverage with no security issues', () => {
			const evaluation: ITestEvaluationOutput = {
				execution_summary: {
					total_tests: 0,
					passed: 0,
					failed: 0
				},
				code_coverage_percentage: 0,
				actionable_recommendations: ['Add initial test coverage'],
				security_issues: [],
				has_severe_security_issues: false
			};

			expect(evaluation.code_coverage_percentage).toBe(0);
			expect(evaluation.security_issues).toHaveLength(0);
			expect(evaluation.has_severe_security_issues).toBe(false);
		});
	});

	describe('IPipelineState', () => {
		it('should track iteration count', () => {
			const state: IPipelineState = {
				status: 'improving_coverage',
				iteration: 3
			};

			expect(state.iteration).toBe(3);
		});

		it('should include error on failure', () => {
			const state: IPipelineState = {
				status: 'failed',
				error: 'Test execution timed out'
			};

			expect(state.status).toBe('failed');
			expect(state.error).toBe('Test execution timed out');
		});
	});
});

describe('JSON Parsing', () => {
	it('should parse valid test scenarios JSON', () => {
		const jsonStr = `{
			"test_scenarios": [
				{
					"scenario_description": "Test user login with valid credentials.",
					"priority": "High"
				},
				{
					"scenario_description": "Test user login with invalid password.",
					"priority": "High"
				}
			]
		}`;

		const parsed = JSON.parse(jsonStr) as ITestScenariosOutput;
		expect(parsed.test_scenarios).toHaveLength(2);
		expect(parsed.test_scenarios[0].scenario_description).toContain('valid credentials');
	});

	it('should parse valid evaluation JSON with security issues', () => {
		const jsonStr = `{
			"execution_summary": {
				"total_tests": 50,
				"passed": 48,
				"failed": 2
			},
			"code_coverage_percentage": 85.0,
			"actionable_recommendations": [
				"Fix failed tests",
				"Increase coverage"
			],
			"security_issues": [
				{
					"severity": "critical",
					"issue": "SQL Injection",
					"location": "db.py:42",
					"recommendation": "Use parameterized queries"
				}
			],
			"has_severe_security_issues": true
		}`;

		const parsed = JSON.parse(jsonStr) as ITestEvaluationOutput;
		expect(parsed.execution_summary.passed).toBe(48);
		expect(parsed.code_coverage_percentage).toBe(85.0);
		expect(parsed.security_issues).toHaveLength(1);
		expect(parsed.security_issues[0].severity).toBe('critical');
		expect(parsed.has_severe_security_issues).toBe(true);
	});

	it('should handle JSON embedded in markdown code blocks', () => {
		const response = `Here is the analysis:

\`\`\`json
{
	"test_scenarios": [
		{"scenario_description": "Test A", "priority": "High"}
	]
}
\`\`\`

This concludes the analysis.`;

		const jsonMatch = response.match(/```(?:json)?\s*([\s\S]*?)```/);
		expect(jsonMatch).not.toBeNull();

		if (jsonMatch) {
			const parsed = JSON.parse(jsonMatch[1].trim()) as ITestScenariosOutput;
			expect(parsed.test_scenarios).toHaveLength(1);
			expect(parsed.test_scenarios[0].scenario_description).toBe('Test A');
		}
	});
});

describe('Pipeline State Transitions', () => {
	it('should transition through all states in order', () => {
		const states: PipelineStatus[] = [
			'pending_identification',
			'awaiting_approval',
			'generating_tests',
			'running_tests',
			'evaluating_results',
			'improving_coverage',
			'completed'
		];

		let currentIndex = 0;
		for (const state of states) {
			expect(states[currentIndex]).toBe(state);
			currentIndex++;
		}
	});

	it('should handle failure state', () => {
		const failedState: IPipelineState = {
			status: 'failed',
			error: 'Network error occurred'
		};

		expect(failedState.status).toBe('failed');
		expect(failedState.error).toBeDefined();
	});

	it('should track improving_coverage state with iteration', () => {
		const improvingState: IPipelineState = {
			status: 'improving_coverage',
			iteration: 5
		};

		expect(improvingState.status).toBe('improving_coverage');
		expect(improvingState.iteration).toBe(5);
	});
});
