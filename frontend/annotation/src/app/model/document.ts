// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject, DBObjects, ModelObject } from "./db";

export interface DBDocument extends DBObject {
    creator_id: string;
    collection_id: string;
    overlap: number;
    text: string;
    metadata: {[key: string]: any};
    has_annotated: {[user_id: string]: boolean};
}

export interface DBDocuments extends DBObjects {
    _items: DBDocument[];
}

export class Document extends ModelObject implements DBDocument {

    public static DEFAULT_PREVIEW_LENGTH = 30;

    public creator_id: string;
    public collection_id: string;
    public overlap: number;
    public text: string;
    public metadata: {[key: string]: any};
    public has_annotated: {[user_id: string]: boolean};
    public _created: any;
    
    public getTextPreview(n: number = Document.DEFAULT_PREVIEW_LENGTH) {
        return `${this.text.slice(0, n)}...`;
    }
    
    public static fromDB(dbObj: DBDocument): Document {
        return <Document>Object.setPrototypeOf(dbObj, new Document());
    }
    
    public static fromDBItems(dbObjs: DBDocuments): Document[] {
        return dbObjs._items.map(Document.fromDB);
    }
}
