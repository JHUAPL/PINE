// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { EventEmitter } from "@angular/core";

import { Observable, of } from "rxjs";

const DEFAULT_BUFFER_SIZE = 1024;

export class BufferedReader {
    // this class reads in a file one chunk at a time and emits each chunk as an observable

    private file: File;
    private bufferSize: number;
    private doCancel = false;

    constructor(file: File, bufferSize = DEFAULT_BUFFER_SIZE) {
        this.file = file;
        this.bufferSize = bufferSize;
        this.doCancel = false;
    }

    public read(): Observable<string> {
        return Observable.create((observer) => {
            const reader = new FileReader();
            let position = 0;
            reader.onload = (e) => {
                observer.next(reader.result);
                if(!this.doCancel && position <= this.file.size) {
                    const blob = this.file.slice(position, position + this.bufferSize);
                    position += this.bufferSize;
                    reader.readAsText(blob);
                } else {
                    observer.complete();
                }
            };
            reader.onerror = (e) => {
                observer.error(e);
                observer.complete();
            };
            if(!this.doCancel) {
                const blob = this.file.slice(position, position + this.bufferSize);
                position += this.bufferSize;
                reader.readAsText(blob);
            } else {
                observer.complete();
            }
        });
    }

    public cancel() {
        this.doCancel = true;
    }

}

export class LineReader {
    // this class uses a buffered reader and emits lines as an observable
    // it is safe with \n, \r, \r\n, and \n\r
    // empty lines will be emitted as empty strings

    private reader: BufferedReader;
    private doCancel: boolean;

    constructor(file: File, bufferSize = DEFAULT_BUFFER_SIZE) {
        this.reader = new BufferedReader(file, bufferSize);
        this.doCancel = false;
    }

    public read(): Observable<string> {
        return Observable.create((observer) => {
            let lastBufferChar = null;
            let remainingBuffer = "";
            this.reader.read().subscribe((buffer: string) => {
                if(this.doCancel) {
                    observer.complete();
                    return;
                }
                // normalize newlines across platforms
                if(lastBufferChar != null) {
                    const b = buffer[0];
                    if((lastBufferChar === "\n" && b === "\r") || (lastBufferChar === "\r" && b === "\n")) {
                        buffer = buffer.substring(1);
                    }
                }
                buffer = buffer.replace(/\r\n|\n\r/g, "\n");
                buffer = buffer.replace(/\r/g, "\n");

                let i = 0;
                let j = buffer.indexOf("\n", i);
                while(!this.doCancel && j !== -1) {
                    let substr = buffer.substring(i, j);
                    if(i === 0 && remainingBuffer.length > 0) {
                        substr = remainingBuffer + substr;
                        remainingBuffer = "";
                    }
                    observer.next(substr);
                    i = j + 1;
                    j = buffer.indexOf("\n", i);
                }
                if(this.doCancel) {
                    observer.complete();
                    return;
                }
                lastBufferChar = buffer[buffer.length - 1];
                if(i < buffer.length) {
                    remainingBuffer += buffer.substring(i);
                }
            }, (error: any) => {
               observer.error(error);
               observer.complete();
            }, () => {
                if(remainingBuffer.length > 0) {
                    observer.next(remainingBuffer);
                    remainingBuffer = "";
                    observer.complete();
                }
            });
        });
    }

    public cancel() {
        this.doCancel = true;
        this.reader.cancel();
    }

}

export class LeftMouseDown {

    private count = 0;

    constructor() {
        document.addEventListener("mousedown", (event: MouseEvent) => { if(this.left(event)) { this.count++; } }, false);
        document.addEventListener("mouseup", (event: MouseEvent) => { if(this.left(event)) { this.count--; } }, false);
    }

    public left(event: MouseEvent) { return event.button === 0; }

    public get(): boolean { return this.count > 0; }

}
