/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Injectable } from '@angular/core';
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

import { BackendService } from "../../service/backend/backend.service";

import { CreatedObject } from "../../model/created";
import { CollectionUserPermissions } from "../../model/collection";
import { DBDocument, DBDocuments, Document } from "../../model/document";
import { DBMeta } from "../../model/db";

export interface PaginatedDocuments {
    documents: Document[],
    meta: DBMeta
}

@Injectable({
    providedIn: 'root'
})
export class DocumentRepositoryService {

    constructor(private backend: BackendService) { }

    getDocumentDetails(docID: string): Observable<Document> {
        return this.backend.get<DBDocument>(`/documents/by_id/${docID}`).pipe(map(Document.fromDB));
    }

    public getCollectionUserPermissions(document_id: string): Observable<CollectionUserPermissions> {
        return this.backend.get<CollectionUserPermissions>(`/documents/user_permissions/${document_id}`);
    }

    public getCountOfDocumentsInCollection(collection_id: string): Observable<number> {
        return this.backend.get<number>(`/documents/count_by_collection_id/${collection_id}`);
    }

    public getAllDocumentsByCollectionID(collection_id: string, truncate: boolean, truncateLength: number = Document.DEFAULT_PREVIEW_LENGTH): Observable<Document[]> {
        let url = `/documents/by_collection_id_all/${collection_id}`;
        if(truncate) {
            url += `?truncate=true&truncateLength=${truncateLength}`;
        }
        return this.backend.get<DBDocuments>(url).pipe(map(Document.fromDBItems));
    }
    
    public getPaginatedDocumentsByCollectionID(collectionId: string,
            page: number, pageSize: number, sortField: string, sortAscending: boolean, filter: string,
            truncate: boolean, truncateLength: number = Document.DEFAULT_PREVIEW_LENGTH): Observable<PaginatedDocuments> {
        let params = {page, pageSize, truncate, truncateLength};
        if(sortField && sortAscending !== undefined) {
            params["sort"] = JSON.stringify({
                "field": sortField,
                "ascending": sortAscending,
            });
        }
        if(filter) params["filter"] = filter;
        return this.backend.get<DBDocuments>(`/documents/by_collection_id_paginated/${collectionId}`, {
            params
        }).pipe(
            map((docs: DBDocuments) => <PaginatedDocuments>{
                documents: Document.fromDBItems(docs),
                meta: docs._meta
            })
        );
    }

    public postDocument(document: Document): Observable<CreatedObject> {
        return this.backend.post<CreatedObject>("/documents", document);
    }

//    public getCanModifyMetadata(document_id: string): Observable<boolean> {
//        return this.backend.get<boolean>(`/documents/can_modify_metadata/${document_id}`);
//    }

    public updateMetadata(document_id: string, metadata: object): Observable<any> {
        return this.backend.put(`/documents/metadata/${document_id}`, metadata);
    }

    public collectionImageUrl(collectionId: string, url: string): string {
        return this.backend.collectionImageUrl(collectionId, url);
    }
}

