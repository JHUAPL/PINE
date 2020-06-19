// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject, DBObjects, ModelObject } from "./db";

export interface DBClassifier extends DBObject {
    collection_id: string;
    labels: string[];
    overlap: number;
    pipeline_id: string;
}

export interface DBClassifiers extends DBObjects {
    _items: DBClassifier[];
}

export class Classifier extends ModelObject implements DBClassifier {

    public collection_id: string;
    public labels: string[];
    public overlap: number;
    public pipeline_id: string;

    public static fromDB(dbObj: DBClassifier): Classifier {
        return <Classifier>Object.setPrototypeOf(dbObj, new Classifier());
    }

    public static fromDBItems(dbObjs: DBClassifiers): Classifier[] {
        return dbObjs._items.map(Classifier.fromDB);
    }
}
