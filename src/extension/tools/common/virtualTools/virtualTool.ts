import type { LanguageModelToolInformation } from 'vscode';

// VirtualTool - dual export for type and value usage
export interface VirtualTool {
	name: string;
	description?: string;
	children?: (LanguageModelToolInformation | VirtualTool)[];
	[key: string]: any;
}

export class VirtualToolClass implements VirtualTool {
	name: string;
	description?: string;
	children?: (LanguageModelToolInformation | VirtualTool)[];

	constructor(name: string, description?: string) {
		this.name = name;
		this.description = description;
	}
}

export const VirtualTool: any = VirtualToolClass;
