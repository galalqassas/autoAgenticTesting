// Stub file for toolCallRound
export interface ToolCallRound {
	id: string;
	toolName: string;
	arguments: unknown;
	result?: unknown;
}

// Export ToolCallRound as both interface and class for different usage patterns
export class ToolCallRoundClass implements ToolCallRound {
	id: string;
	toolName: string;
	arguments: unknown;
	result?: unknown;

	constructor(id: string, toolName: string, args: unknown) {
		this.id = id;
		this.toolName = toolName;
		this.arguments = args;
	}
}

export const ToolCallRound: any = ToolCallRoundClass;

export class ToolCallRoundCollection {
	private rounds: ToolCallRound[] = [];

	add(round: ToolCallRound): void {
		this.rounds.push(round);
	}

	getAll(): ToolCallRound[] {
		return this.rounds;
	}
}
