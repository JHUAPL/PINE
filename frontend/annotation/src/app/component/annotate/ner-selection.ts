/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import tippy from "tippy.js";

import { Word } from "../../model/word";

import { NerData } from "./ner-data";

export class NerSelection {

    private allowOverlappingAnnotations;
    private words: Word[];

    constructor() {
        this.allowOverlappingAnnotations = true;
        this.words = [];
    }

    public setAllowOverlappingAnnotations(allowOverlappingAnnotations: boolean) {
        this.allowOverlappingAnnotations = allowOverlappingAnnotations;
    }

    public isEmpty() {
        return this.words.length === 0;
    }

    public clear(destroyTippy: boolean) {
        for(const word of this.words) {
            word.elem.classList.remove("selectLeft");
            word.elem.classList.remove("selectRight");
            word.elem.classList.remove("select");
            if(destroyTippy) {
                (<any>word.elem)._tippy.destroy();
            }
        }
        const clone = this.words;
        this.words = [];
        return clone;
    }

    public start(word: Word) {
        if(!this.isEmpty()) {
            throw new Error("Selection is non-empty (shouldn't happen).");
        }
        this.words.push(word);
        word.elem.classList.add("selectLeft", "select", "selectRight");
    }

    public contains(word: Word) {
        for(const w of this.words) {
            if(w.index === word.index) { return true; }
        }
        return false;
    }

    private goingLeft(word: Word) {
        return word.index < this.words[0].index;
    }

    public canAdd(nerData: NerData, word: Word): boolean {
        if(this.isEmpty() || this.contains(word)) {
            return false;
        }
        if(!this.allowOverlappingAnnotations && word.elem.classList && word.elem.classList.contains("annotation")) {
            return false;
        }

        if(this.goingLeft(word)) {
            for(let i = this.words[0].index - 1; i >= 0; i--) {
                if(i === word.index) { return true; }
                if(!/^\s+$/.test(nerData.words[i].text)) { return false; }
            }
            return false;
        } else {
            for(let i = this.words[this.words.length - 1].index + 1; i < nerData.words.length; i++) {
                if(i === word.index) { return true; }
                if(!/^\s+$/.test(nerData.words[i].text)) { return false; }
            }
            return false;
        }
    }

    public add(nerData: NerData, word: Word) {
        if(!this.canAdd(nerData, word)) {
            throw new Error("Can't add to selection (shouldn't happen).");
        }

        if(this.goingLeft(word)) {
            this.words[0].elem.classList.remove("selectLeft");
            for(let i = this.words[0].index - 1; i >= word.index; i--) {
                const docWord = nerData.words[i];
                docWord.elem.classList.add("select");
                if(i === word.index) {
                    docWord.elem.classList.add("selectLeft");
                } else {
                    docWord.elem.classList.remove("selectLeft");
                }
                this.words.unshift(docWord);
            }
        } else {
            this.words[this.words.length - 1].elem.classList.remove("selectRight");
            for(let i = this.words[this.words.length - 1].index + 1; i <= word.index; i++) {
                const docWord = nerData.words[i];
                docWord.elem.classList.add("select");
                if(i === word.index) {
                    docWord.elem.classList.add("selectRight");
                } else {
                    docWord.elem.classList.remove("selectRight");
                }
                this.words.push(docWord);
            }
        }
    }

    public addTippy(builder) {
        for(const word of this.words) {
            tippy(word.elem, builder(word));
        }
    }

}
