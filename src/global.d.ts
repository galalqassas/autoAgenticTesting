declare const crypto: any;
declare const TextDecoder: any;
type Timeout = any;
interface IdleApi {
    requestIdleCallback(handler: any, options?: any): any;
    cancelIdleCallback(handle: any): void;
}
declare const globalThis: IdleApi & typeof globalThis;
