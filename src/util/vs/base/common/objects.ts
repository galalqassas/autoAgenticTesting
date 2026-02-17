//!!! DO NOT modify, this file was COPIED from 'microsoft/vscode'

/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { isTypedArray, isObject, isUndefinedOrNull } from './types';

export function deepClone<T>(obj: T): T {
	if (!obj || typeof obj !== 'object') {
		return obj;
	}
	if (obj instanceof RegExp) {
		return obj;
	}
	if (Array.isArray(obj)) {
		return obj.map(item => deepClone(item)) as unknown as T;
	}
	const result: Record<string, unknown> = {};
	Object.entries(obj as Record<string, unknown>).forEach(([key, value]) => {
		result[key] = value && typeof value === 'object' ? deepClone(value) : value;
	});
	return result as T;
}

export function deepFreeze<T>(obj: T): T {
	if (!obj || typeof obj !== 'object') {
		return obj;
	}
	const stack: unknown[] = [obj];
	while (stack.length > 0) {
		const obj = stack.shift() as Record<string, unknown>;
		Object.freeze(obj);
		for (const key in obj) {
			if (_hasOwnProperty.call(obj, key)) {
				const prop = obj[key];
				if (typeof prop === 'object' && prop !== null && !Object.isFrozen(prop) && !isTypedArray(prop)) {
					stack.push(prop);
				}
			}
		}
	}
	return obj;
}

const _hasOwnProperty = Object.prototype.hasOwnProperty;


export function cloneAndChange(obj: unknown, changer: (orig: unknown) => unknown): unknown {
	return _cloneAndChange(obj, changer, new Set());
}

function _cloneAndChange(obj: unknown, changer: (orig: unknown) => unknown, seen: Set<unknown>): unknown {
	if (isUndefinedOrNull(obj)) {
		return obj;
	}

	const changed = changer(obj);
	if (typeof changed !== 'undefined') {
		return changed;
	}

	if (Array.isArray(obj)) {
		const r1: unknown[] = [];
		for (const e of obj) {
			r1.push(_cloneAndChange(e, changer, seen));
		}
		return r1;
	}

	if (isObject(obj)) {
		if (seen.has(obj)) {
			throw new Error('Cannot clone recursive data-structure');
		}
		seen.add(obj);
		const r2: Record<string, unknown> = {};
		const source = obj as Record<string, unknown>;
		for (const i2 in source) {
			if (_hasOwnProperty.call(source, i2)) {
				r2[i2] = _cloneAndChange(source[i2], changer, seen);
			}
		}
		seen.delete(obj);
		return r2;
	}

	return obj;
}

/**
 * Copies all properties of source into destination. The optional parameter "overwrite" allows to control
 * if existing properties on the destination should be overwritten or not. Defaults to true (overwrite).
 */
export function mixin(destination: unknown, source: unknown, overwrite: boolean = true): unknown {
	if (!isObject(destination)) {
		return source;
	}

	if (isObject(source)) {
		const dest = destination as Record<string, unknown>;
		const src = source as Record<string, unknown>;
		Object.keys(src).forEach(key => {
			if (key in dest) {
				if (overwrite) {
					if (isObject(dest[key]) && isObject(src[key])) {
						mixin(dest[key], src[key], overwrite);
					} else {
						dest[key] = src[key];
					}
				}
			} else {
				dest[key] = src[key];
			}
		});
	}
	return destination;
}

export function equals(one: unknown, other: unknown): boolean {
	if (one === other) {
		return true;
	}
	if (one === null || one === undefined || other === null || other === undefined) {
		return false;
	}
	if (typeof one !== typeof other) {
		return false;
	}
	if (typeof one !== 'object') {
		return false;
	}
	if ((Array.isArray(one)) !== (Array.isArray(other))) {
		return false;
	}

	let i: number;
	let key: string;

	if (Array.isArray(one)) {
		const otherArray = other as unknown[];
		if (one.length !== otherArray.length) {
			return false;
		}
		for (i = 0; i < one.length; i++) {
			if (!equals(one[i], otherArray[i])) {
				return false;
			}
		}
	} else {
		const oneObj = one as Record<string, unknown>;
		const otherObj = other as Record<string, unknown>;
		const oneKeys: string[] = [];

		for (key in oneObj) {
			oneKeys.push(key);
		}
		oneKeys.sort();
		const otherKeys: string[] = [];
		for (key in otherObj) {
			otherKeys.push(key);
		}
		otherKeys.sort();
		if (!equals(oneKeys, otherKeys)) {
			return false;
		}
		for (i = 0; i < oneKeys.length; i++) {
			if (!equals(oneObj[oneKeys[i]], otherObj[oneKeys[i]])) {
				return false;
			}
		}
	}
	return true;
}

/**
 * Calls `JSON.Stringify` with a replacer to break apart any circular references.
 * This prevents `JSON`.stringify` from throwing the exception
 *  "Uncaught TypeError: Converting circular structure to JSON"
 */
export function safeStringify(obj: unknown): string {
	const seen = new Set<unknown>();
	return JSON.stringify(obj, (key, value) => {
		if (isObject(value) || Array.isArray(value)) {
			if (seen.has(value)) {
				return '[Circular]';
			} else {
				seen.add(value);
			}
		}
		if (typeof value === 'bigint') {
			return `[BigInt ${value.toString()}]`;
		}
		return value;
	});
}

type obj = { [key: string]: unknown };
/**
 * Returns an object that has keys for each value that is different in the base object. Keys
 * that do not exist in the target but in the base object are not considered.
 *
 * Note: This is not a deep-diffing method, so the values are strictly taken into the resulting
 * object if they differ.
 *
 * @param base the object to diff against
 * @param obj the object to use for diffing
 */
export function distinct(base: obj, target: obj): obj {
	const result = Object.create(null);

	if (!base || !target) {
		return result;
	}

	const targetKeys = Object.keys(target);
	targetKeys.forEach(k => {
		const baseValue = base[k];
		const targetValue = target[k];

		if (!equals(baseValue, targetValue)) {
			result[k] = targetValue;
		}
	});

	return result;
}

export function getCaseInsensitive(target: obj, key: string): unknown {
	const lowercaseKey = key.toLowerCase();
	const equivalentKey = Object.keys(target).find(k => k.toLowerCase() === lowercaseKey);
	return equivalentKey ? target[equivalentKey] : target[key];
}

export function filter(obj: obj, predicate: (key: string, value: unknown) => boolean): obj {
	const result = Object.create(null);
	for (const [key, value] of Object.entries(obj)) {
		if (predicate(key, value)) {
			result[key] = value;
		}
	}
	return result;
}

export function mapValues<T extends {}, R>(obj: T, fn: (value: T[keyof T], key: string) => R): { [K in keyof T]: R } {
	const result: { [key: string]: R } = {};
	for (const [key, value] of Object.entries(obj)) {
		result[key] = fn(<T[keyof T]>value, key);
	}
	return result as { [K in keyof T]: R };
}
