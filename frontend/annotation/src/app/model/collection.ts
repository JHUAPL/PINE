// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject, DBObjects, ModelObject } from "./db";

export const METADATA_TITLE = "title";
export const CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS = "allow_overlapping_ner_annotations";

export interface DBCollection extends DBObject {

    creator_id: string;
    annotators: string[];
    viewers: string[];
    labels: string[];
    metadata: { [s: string]: any; };
    archived: boolean;
    configuration: { [s: string]: any; };

}

export interface DBCollections extends DBObjects {
    _items: DBCollection[];
}

export class Collection extends ModelObject implements DBCollection {

    public creator_id: string;
    public annotators: string[];
    public viewers: string[];
    public labels: string[];
    public metadata: { [s: string]: any; };
    public archived: boolean;
    public configuration: { [s: string]: any; };
    
    public hasTitle() {
        return this.metadata && this.metadata.hasOwnProperty(METADATA_TITLE);
    }
    
    public getTitle() {
        return this.hasTitle() ? this.metadata[METADATA_TITLE] : "";
    }
    
    public getTitleOrId() {
        if(this.hasTitle()) {
            return this.getTitle();
        } else {
            return `"<ID ${this._id}>`;
        }
    }
    
    public getAllowOverlappingNerAnnotations(ifNotSpecified: boolean = true): boolean {
        if(this.configuration && CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS in this.configuration) {
            return <boolean>this.configuration[CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS];
        } else {
            return ifNotSpecified;
        }
    }

    public static sortByTitleAndId(collections: Collection[]) {
        collections.sort((a: Collection, b: Collection) => {
            let titleComp = a.getTitle().localeCompare(b.getTitle());
            if(titleComp != 0) return titleComp;
            else return a._id.localeCompare(b._id);
        });
    }
    
    public static fromDB(dbObj: DBCollection): Collection {
        return <Collection>Object.setPrototypeOf(dbObj, new Collection());
    }

    public static fromDBItems(dbObjs: DBCollections): Collection[] {
        return dbObjs._items.map(Collection.fromDB);
    }
}

export interface DownloadCollectionData {
    include_collection_metadata: boolean;
    include_document_metadata: boolean;
    include_document_text: boolean;
    include_annotations: boolean;
    include_annotation_latest_version_only: boolean;
    as_file: boolean;
}
