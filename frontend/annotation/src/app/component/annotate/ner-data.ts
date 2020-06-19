/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { EventEmitter } from "@angular/core";

import { NerAnnotation } from "../../model/annotation";
import { Word } from "../../model/word";

export class NerData {

    public changed: EventEmitter<NerAnnotation[]>;

    public words: Word[];
    public annotations: NerAnnotation[];
    private wordIndices: object;

    constructor() {
        this.changed = new EventEmitter<NerAnnotation[]>();
        this.words = [];
        this.annotations = [];
        this.wordIndices = {};
    }

    public setWordsAndAnnotations(words: Word[], annotations: NerAnnotation[]) {
        this.words = words;
        this.setAnnotations(annotations);
    }
    
    public setAnnotations(annotations: NerAnnotation[]) {
        this.annotations = annotations.slice();
        for(const annotation of annotations) {
            this.mapAnnotation(annotation);
        }
    }

    private mapAnnotation(annotation: NerAnnotation) {
        const id = this.id(annotation);
        for(const word of this.words) {
            if(word.start >= annotation.start && word.end <= annotation.end) {
                if(this.wordIndices[id]) {
                    this.wordIndices[id][1] = word.index;
                } else {
                    this.wordIndices[id] = [word.index, word.index];
                }
            } else if(word.end > annotation.end) {
                break;
            }
        }
    }

    public emitChanged() {
        this.changed.emit(this.annotations);
    }

    public addOrUpdateAnnotation(annotation: NerAnnotation) {
        for(const a of this.annotations) {
            if(a.start === annotation.start && a.end === annotation.end) {
                if(a.label === annotation.label) {
                    return false;
                }
                // Ignoring check for update, just adding all annotations for now, should allow for multiple annotations of same word
                // else {
                //     a.label = annotation.label;
                //     return true;
                // }
            }
        }
        this.annotations.push(annotation);
        this.mapAnnotation(annotation);
        return true;
    }

    public removeAnnotation(annotation: NerAnnotation) {
        for(let i = 0; i < this.annotations.length; i++) {
            if(this.annotations[i].start === annotation.start &&
                    this.annotations[i].end === annotation.end &&
                    this.annotations[i].label === annotation.label) {
                delete this.wordIndices[this.id(this.annotations[i])];
                this.annotations.splice(i, 1);
                return true;
            }
        }
        return false;
    }

    public removeAllAnnotations() {
        this.annotations = [];
        this.wordIndices = {};
    }

    public wordsIn(annotation: NerAnnotation) {
        const i = this.wordIndices[this.id(annotation)];
        return this.words.slice(i[0], i[1] + 1);
    }

    public annotationsWith(word: Word) {
        const a = [];
        for(const annotation of this.annotations) {
            const i = this.wordIndices[this.id(annotation)];
            if(word.index >= i[0] && word.index <= i[1]) {
                a.push(annotation);
            }
        }
        return a;
    }

    // Added label to id to make each id unique if annotating same word, necessary for annotation map
    private id(annotation: NerAnnotation) {
        return `${annotation.start}_${annotation.end}_${annotation.label}`;
    }

}
