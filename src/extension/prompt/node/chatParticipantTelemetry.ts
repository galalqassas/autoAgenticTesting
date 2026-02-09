// Chat telemetry stubs with dual export pattern
export interface ChatParticipantTelemetry {
	[key: string]: any;
}
export const ChatParticipantTelemetry: any = {};

export interface ChatTelemetryBuilder {
	build(): any;
	[key: string]: any;
}
export const ChatTelemetryBuilder: any = {};
