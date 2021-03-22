/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Injectable } from "@angular/core";
import { HttpResponse, HttpEvent, HttpEventType } from "@angular/common/http";

import { Observable, forkJoin } from "rxjs";
import { map, flatMap } from "rxjs/operators";

import { AppConfig } from "../../app.config";
import { BackendService } from "../backend/backend.service";

import { DBCollection, DBCollections, Collection, CollectionUserPermissions, DownloadCollectionData } from "../../model/collection";
import { CreatedObject } from "../../model/created";

@Injectable({
    providedIn: "root"
})
export class CollectionRepositoryService {

    constructor(private backend: BackendService) { }

//    public getMyUnarchivedCollections(): Observable<Collection[]> {
//        return this.backend.get<DBCollections>("/collections/unarchived").pipe(map(Collection.fromDBItems));
//    }

    public getMyUnarchivedCollectionsPaginated(): Observable<Collection> {
        return this.backend.getItemsPaginated((page: number) => {
            return this.backend.get<DBCollections>(`/collections/unarchived/${page}`);
        }).pipe(map(Collection.fromDB));
    }

//    public getMyArchivedCollections(): Observable<Collection[]> {
//        return this.backend.get<DBCollections>("/collections/archived").pipe(map(Collection.fromDBItems));
//    }

    public getMyArchivedCollectionsPaginated(): Observable<Collection> {
        return this.backend.getItemsPaginated((page: number) => {
            return this.backend.get<DBCollections>(`/collections/archived/${page}`);
        }).pipe(map(Collection.fromDB));
    }

    public getUserPermissions(collection_id: string): Observable<CollectionUserPermissions> {
        return this.backend.get<CollectionUserPermissions>(`/collections/user_permissions/${collection_id}`);
    }

    public getCollectionDetails(colID: string): Observable<Collection> {
        return this.backend.get<DBCollection>("/collections/by_id/" + colID).pipe(map(Collection.fromDB));
    }

    private makePostCollectionData(collection: Collection, csvFile: File, csvTextCol: number, csvHasHeader: boolean, imageFiles: FileList,
            overlap: number, train_every: number, pipelineId: string, classifierParameters: object = {}): FormData {
        const input = new FormData();
        if(csvFile != null) {
            input.append("file", csvFile, csvFile.name);
            input.append("csvTextCol", JSON.stringify(csvTextCol));
            input.append("csvHasHeader", JSON.stringify(csvHasHeader));
        }
        if(imageFiles) {
            for(let i = 0; i < imageFiles.length; i++) {
                input.append(`imageFile${i}`, imageFiles[i], imageFiles[i].name);
            }
        }
        input.append("collection", JSON.stringify(collection));
        input.append("train_every", JSON.stringify(train_every));
        input.append("overlap", JSON.stringify(overlap));
        input.append("pipelineId", JSON.stringify(pipelineId));
        input.append("classifierParameters", JSON.stringify(classifierParameters));
        return input;
    }

    public postCollection(collection: Collection, csvFile: File, csvTextCol: number, csvHasHeader: boolean, imageFiles: FileList,
            overlap: number, train_every: number, pipelineId: string, classifierParameters: object = {}): Observable<Collection> {
        const input = this.makePostCollectionData(collection, csvFile, csvTextCol, csvHasHeader, imageFiles,
            overlap, train_every, pipelineId, classifierParameters);
        return this.backend.postForm<CreatedObject>("/collections", input).pipe(flatMap(
                (createdCollection: CreatedObject) => this.getCollectionDetails(createdCollection._id)));
    }

    public postCollectionWithProgress(collection: Collection, csvFile: File, csvTextCol: number, csvHasHeader: boolean, imageFiles: FileList,
            overlap: number, train_every: number, pipelineId: string, classifierParameters: object = {}): Observable<HttpEvent<CreatedObject>> {
        const input = this.makePostCollectionData(collection, csvFile, csvTextCol, csvHasHeader, imageFiles,
            overlap, train_every, pipelineId, classifierParameters);
        return this.backend.postFormWithProgress<CreatedObject>("/collections", input);
    }

    public addAnnotatorToCollection(colId: string, new_annotator: string): Observable<Collection> {
        const input = new FormData();
        input.append("user_id", JSON.stringify(new_annotator));
        return this.backend.postForm<any>("/collections/add_annotator/" + colId, input).pipe(map(Collection.fromDB));
    }

    public addViewerToCollection(colId: string, new_viewer: string): Observable<Collection> {
        const input = new FormData();
        input.append("user_id", JSON.stringify(new_viewer));
        return this.backend.postForm<any>("/collections/add_viewer/" + colId, input).pipe(map(Collection.fromDB));
    }

    public addLabelToCollection(colId: string, new_label: string): Observable<Collection> {
        const input = new FormData();
        input.append("new_label", JSON.stringify(new_label));
        return this.backend.postForm<any>("/collections/add_label/" + colId, input).pipe(map(Collection.fromDB));
    }

    public archiveCollection(collection_id: string): Observable<Collection> {
        return this.backend.put<DBCollection>("/collections/archive/" + collection_id, {}).pipe(map(Collection.fromDB));
    }

    public unarchiveCollection(collection_id: string): Observable<Collection> {
        return this.backend.put<DBCollection>("/collections/unarchive/" + collection_id, {}).pipe(map(Collection.fromDB));
    }
    
    public downloadData(collection_id: string, data: DownloadCollectionData): Observable<HttpResponse<Blob>> {
        data.as_file = true;
        return this.backend.getBlob("/collections/by_id/" + collection_id + "/download", {
            params: data
        });
    }

    public getCollectionImageExists(collection_id: string, path: string): Observable<boolean> {
        return this.backend.get<boolean>(`/collections/image_exists/${collection_id}/${path}`);
    }

    public uploadCollectionImage(collection_id: string, path: string, file: File): Observable<string> {
        const formData = new FormData();
        formData.append("file", file);
        return this.backend.post<string>(`/collections/image/${collection_id}/${path}`, formData);
    }

    public collectionImageUrl(collectionId: string, url: string): string {
        return this.backend.collectionImageUrl(collectionId, url);
    }

    public getCollectionImages(collectionId: string, includeStatic: boolean = false): Observable<string[]> {
        if(!includeStatic) {
            return this.backend.get<string[]>(`/collections/images/${collectionId}`);
        } else {
            forkJoin(
                this.backend.get<string[]>(`/collections/images/${collectionId}`),
                this.backend.get<string[]>(`/collections/static_images/${collectionId}`)
            ).pipe(map(([res1, res2]: [string[], string[]]) => res1.concat(res2)));
        }
    }
}
