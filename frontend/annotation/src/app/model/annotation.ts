// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { Observable } from "rxjs";

import { DBObject, DBObjects, ModelObject } from "./db";
import { DocLabel } from "./doclabel";

export interface NerAnnotation {
    start: number;
    end: number;
    label: string;
}

export interface DBAnnotation extends DBObject {
    creator_id: string;
    collection_id: string;
    document_id: string;
    annotation: (string | NerAnnotation)[];
}

export interface DBAnnotations extends DBObjects {
    _items: DBAnnotation[];
}

export class Annotation extends ModelObject implements DBAnnotation {
    public creator_id: string;
    public collection_id: string;
    public document_id: string;
    public annotation: (string | NerAnnotation)[];

    public static fromDB(dbObj: DBAnnotation): Annotation {
        return <Annotation>Object.setPrototypeOf(dbObj, new Annotation());
    }

    public static fromDBItems(dbObjs: DBAnnotations): Annotation[] {
        return dbObjs._items.map(Annotation.fromDB);
    }
    
    public static isDocLabel(annotation: any): boolean {
        return typeof annotation === "string" || annotation instanceof String;
    }
    
    public static getDocLabel(annotation: any): string {
        return <string>annotation;
    }
    
    public static isNerAnnotation(annotation: any): boolean {
        return Object.prototype.toString.call(annotation) === '[object Array]' && annotation.length === 3;
    }
    
    public static getNerAnnotation(annotation: any): NerAnnotation {
        return <NerAnnotation>{
            start: annotation[0],
            end: annotation[1],
            label: annotation[2]
        };
    }
    
    public static getDocLabels(annotations: Annotation[]): string[] {
        const ret = [];
        for(const annotation of annotations) {
            for(const ann of annotation.annotation) {
                if(Annotation.isDocLabel(ann)) {
                    const label = Annotation.getDocLabel(ann);
                    if(!ret.includes(label)) {
                        ret.push(label);
                    }
                }
            }
        }
        return ret;
    }
    
    public static getDocLabelsMap(annotations: Annotation[]): { [s: string]: string[]; } {
        const ret = {};
        for(const annotation of annotations) {
            if(!(annotation.creator_id in ret)) {
                ret[annotation.creator_id] = [];
            }
            for(const ann of annotation.annotation) {
                if(Annotation.isDocLabel(ann)) {
                    const label = Annotation.getDocLabel(ann);
                    ret[annotation.creator_id].push(label);
                }
            }
        }
        return ret;
    }
    
    public static getNerAnnotationsMap(annotations: Annotation[]): { [s: string]: NerAnnotation[]; } {
        const ret = {};
        for(const annotation of annotations) {
            if(!(annotation.creator_id in ret)) {
                ret[annotation.creator_id] = [];
            }
            for(const ann of annotation.annotation) {
                if(Annotation.isNerAnnotation(ann)) {
                    const nerAnn = Annotation.getNerAnnotation(ann);
                    ret[annotation.creator_id].push(nerAnn);
                }
            }
        }
        return ret;
    }
    
    public static getNerAnnotations(annotations: Annotation[]): NerAnnotation[] {
        const ret = [];
        for(const annotation of annotations) {
            for(const ann of annotation.annotation) {
                if(Annotation.isNerAnnotation(ann)) {
                    const nerAnn = Annotation.getNerAnnotation(ann);
                    if(!ret.includes(nerAnn)) {
                        ret.push(nerAnn);
                    }
                }
            }
        }
        return ret;
    }
}
