// Linkify service stubs with dual export pattern
export interface ILinkifyService {
	[key: string]: any;
}
export const ILinkifyService: any = 'ILinkifyService';

export interface IContributedLinkifierFactory {
	create(): any;
	[key: string]: any;
}
export const IContributedLinkifierFactory: any = {};
