// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import * as _ from "lodash";
import { Observable } from "rxjs";

export class Word {

    public id: string;
    public end: number;
    public innerHTML: string = undefined;
    public elem: HTMLElement = undefined;

    constructor(public start: number, public text: string, public index: number) {
        this.end = start + text.length;
        this.id = "word_" + this.start + "_" + this.end;
    }

    public static parseWords(input: string): Observable<string> {
        return Observable.create((observer) => {
            let index = 0;
            //Split on all punctuation and spaces to allow for more control
            for(const chunk of input.split(/(?=[^\w]|\b)/)) {
                // handles both \n and \r\n but not \r alone
                let i = 0;
                while(i < chunk.length) {
                    let j = chunk.indexOf('\n', i);
                    if(j === -1) { // end of chunk
                        j = chunk.length;
                        observer.next(chunk.slice(i, j));
                    } else if(i === j) { // \n
                        observer.next(chunk.slice(i, j + 1));
                    } else if(i < j && chunk[j - 1] === '\r') { // word\r\n
                        observer.next(chunk.slice(i, j - 1));
                        observer.next(chunk.slice(j - 1, j + 1));
                    } else { // word\n
                        observer.next(chunk.slice(i, j));
                        observer.next(chunk.slice(j, j + 1));
                    }
                    i = j + 1;
                }
                index += chunk.length;
            }
            observer.complete();
        });
    }
    
    public static parseWordObjects(input: string): Word[] {
        let index = 0;
        const words = [];
        Word.parseWords(input).subscribe((word: string) => {
            let wordObj = new Word(index, word, words.length);
            if(word === "\t") {
                wordObj.innerHTML = "&nbsp;&nbsp;&nbsp;&nbsp;";
            } else if(word === "\n" || word === "\r" || word === "\n\r" || word === "\r\n") {
                wordObj.innerHTML = "<br />";
            }
            words.push(wordObj);
            index += word.length;
        });
        return words;
    }

	public static parseWordObjectsFromHtml(elems: HTMLElement[]): Word[] {
        const words = [];
		_.forEach(elems, (elem: HTMLElement) => {
			console.log(elem);
			let id = elem.getAttribute('ID');
			let parts = id.split('_');
			let start = parts[1];
			//let end = parts[2];
			let wordObj = new Word(+start, elem.innerHTML, words.length);
			words.push(wordObj);
		});
		return words;
	}

}

