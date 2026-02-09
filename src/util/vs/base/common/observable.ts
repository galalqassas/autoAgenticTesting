export interface IObservable<T, TChange = unknown> {
	get(): T;
	addObserver(observer: IObserver): void;
	removeObserver(observer: IObserver): void;
	reportChanges(): void;
}
export interface IObservableWithChange<T, TChange> extends IObservable<T, TChange> {}
export interface IObserver {
	beginUpdate<T>(observable: IObservable<T>): void;
	endUpdate<T>(observable: IObservable<T>): void;
	handlePossibleChange<T>(observable: IObservable<T>): void;
	handleChange<T, TChange>(observable: IObservable<T>, change: TChange): void;
}
export const observableValue: any = () => {};
export const transaction: any = () => {};
