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

export interface CollectionUserPermissions {
    // this class should be updated in the following places:
    // * backend/pine/backend/models.py
    // * client/pine/client/models.py
    // * frontend/annotation/src/app/model/collection.ts
    view: boolean;
    annotate: boolean;
    add_documents: boolean;
    add_images: boolean;
    modify_users: boolean;
    modify_labels: boolean;
    modify_document_metadata: boolean;
    download_data: boolean;
    archive: boolean;
}

export function newPermissions(): CollectionUserPermissions {
    return <CollectionUserPermissions>{
        view: false,
        annotate: false,
        add_documents: false,
        add_images: false,
        modify_users: false,
        modify_labels: false,
        modify_document_metadata: false,
        download_data: false,
        archive: false
    };
}

export const PERMISSION_TITLES = {
    view: "View Documents",
    annotate: "Annotate Documents",
    add_documents: "Add Documents",
    add_images: "Add Images",
    modify_users: "Modify Viewers/Annotators",
    modify_labels: "Modify Collection Labels",
    modify_document_metadata: "Modify Document Metadata",
    download_data: "Download Collection Data",
    archive: "Archive/Unarchive Collection"
};

export interface DownloadCollectionData {
    include_collection_metadata: boolean;
    include_document_metadata: boolean;
    include_document_text: boolean;
    include_annotations: boolean;
    include_annotation_latest_version_only: boolean;
    as_file: boolean;
}
