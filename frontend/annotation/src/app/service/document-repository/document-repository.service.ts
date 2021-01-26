import { Injectable } from '@angular/core';
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

import { BackendService } from "../../service/backend/backend.service";

import { CreatedObject } from "../../model/created";
import { DBDocument, DBDocuments, Document } from "../../model/document";

@Injectable({
    providedIn: 'root'
})
export class DocumentRepositoryService {

    constructor(private backend: BackendService) { }

    getDocumentDetails(docID: string): Observable<Document> {
        return this.backend.get<DBDocument>(`/documents/by_id/${docID}`).pipe(map(Document.fromDB));
    }

    getUserCanAnnotate(docId: string): Observable<boolean> {
        return this.backend.get<boolean>("/documents/can_annotate/" + docId);
    }

//    getDocumentsByCollectionID(colID: string): Observable<Document[]> {
//        return this.backend.get<DBDocuments>(`/documents/by_collection_id/${colID}`).pipe(map(Document.fromDBItems));
//    }

    public getDocumentsByCollectionID(collection_id: string, truncate: boolean, truncateLength: number = Document.DEFAULT_PREVIEW_LENGTH): Observable<Document[]> {
        let url = `/documents/by_collection_id/${collection_id}`;
        if(truncate) {
            url += `?truncate=true&truncateLength=${truncateLength}`;
        }
        return this.backend.get<DBDocuments>(url).pipe(map(Document.fromDBItems));
    }
    
    public getDocumentsByCollectionIDPaginated(collection_id: string, truncate: boolean, truncateLength: number = Document.DEFAULT_PREVIEW_LENGTH): Observable<Document> {
        return this.backend.getItemsPaginated((page: number) => {
            let url = `/documents/by_collection_id/${collection_id}/${page}`;
            if(truncate) {
                url += `?truncate=true&truncateLength=${truncateLength}`;
            }
            return this.backend.get<DBDocuments>(url);
        }).pipe(map(Document.fromDB));
    }

    public postDocument(document: Document): Observable<CreatedObject> {
        return this.backend.post<CreatedObject>("/documents", document);
    }

    public getCanModifyMetadata(document_id: string): Observable<boolean> {
        return this.backend.get<boolean>(`/documents/can_modify_metadata/${document_id}`);
    }

    public updateMetadata(document_id: string, metadata: object): Observable<any> {
        return this.backend.put(`/documents/metadata/${document_id}`, metadata);
    }

    public collectionImageUrl(collectionId: string, url: string): string {
        return this.backend.collectionImageUrl(collectionId, url);
    }
}

