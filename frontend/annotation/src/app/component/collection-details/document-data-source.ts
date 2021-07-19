/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { ElementRef, OnDestroy } from "@angular/core";
import { CollectionViewer, DataSource } from "@angular/cdk/collections";
import { MatPaginator, MatSort } from "@angular/material";
import { HttpErrorResponse } from "@angular/common/http";

import { Observable, BehaviorSubject, Subscription, forkJoin, merge, fromEvent } from "rxjs";
import { take, debounceTime, distinctUntilChanged, tap } from "rxjs/operators";

import { Document } from "../../model/document";
import { IAAReport } from "../../model/iaareport";

import { AuthService } from "../../service/auth/auth.service";
import { DocumentRepositoryService, PaginatedDocuments } from "../../service/document-repository/document-repository.service";
import { IaaReportingService } from "../../service/iaa-reporting/iaa-reporting.service";

export interface DocumentRow {
    id: string;
    creator: string;
    last_updated: Date;
    text_start: string;
    annotated: boolean;
    ann_agreement: number;
}

const fieldMapping: {[column: string]: string} = {
    "id": "_id",
    "creator": "creator_id",
    "last_updated": "_updated",
    "text_start": "text"
}

export class DocumentDataSource implements OnDestroy, DataSource<DocumentRow> {

    private documentSubject = new BehaviorSubject<DocumentRow[]>([]);
    private loadingSubject = new BehaviorSubject<boolean>(false);
    private subscription: Subscription;

    public loading$ = this.loadingSubject.asObservable();
    public collectionReport: IAAReport;
    public length: number;

    public latestError: string = null;

    constructor(private documentService: DocumentRepositoryService,
                private auth: AuthService,
                private iaa: IaaReportingService,
                private collectionId: string = null,
                public truncate: boolean = true,
                public truncateLength: number = Document.DEFAULT_PREVIEW_LENGTH) { }

    ngOnDestroy() {
        if(this.subscription) {
            this.subscription.unsubscribe();
            this.subscription = undefined;
        }
    }

    connect(_: CollectionViewer): Observable<DocumentRow[]> {
        return this.documentSubject.asObservable();
    }

    disconnect(_: CollectionViewer): void {
        this.documentSubject.complete();
        this.loadingSubject.complete();
    }

    public setPaginatorSortAndFilter(paginator: MatPaginator, sort: MatSort, filter: ElementRef) {
        if(this.subscription) {
            this.subscription.unsubscribe();
        }
        this.loadFrom(paginator, sort, filter);
        this.subscription =
            merge(
                paginator.page,
                sort.sortChange.pipe(
                    tap(() => paginator.pageIndex = 0)),
                fromEvent(filter.nativeElement, "keyup").pipe(
                    debounceTime(500),
                    distinctUntilChanged(),
                    tap(() => paginator.pageIndex = 0))
            ).subscribe((_) => {
                this.loadFrom(paginator, sort, filter);
            }, (error: Error) => {
                console.error(error);
                this.latestError = error.message;
            });
    }

    public setCollection(collectionId: string): Observable<boolean> {
        this.loadingSubject.next(true);
        this.latestError = null;
        return new Observable<boolean>((observer) => {
            this.collectionId = collectionId;
            forkJoin(
                this.iaa.getIIAReportByCollection(this.collectionId),
                this.documentService.getCountOfDocumentsInCollection(this.collectionId)
            ).pipe(take(1)).subscribe(([reports, length]: [IAAReport[], number]) => {
                this.collectionReport = reports[0];
                this.length = length;
                observer.next(true);
            }, (error: HttpErrorResponse) => {
                this.latestError = error.message;
                observer.error(error);
            }, () => {
                observer.complete();
                this.loadingSubject.next(false);
            });
        });
    }

    private loadFrom(paginator: MatPaginator, sort: MatSort, filter: ElementRef) {
        this.load(
            paginator.pageIndex,
            paginator.pageSize,
            sort.direction ? fieldMapping[sort.active] : undefined,
            sort.direction === "asc",
            filter.nativeElement.value ? filter.nativeElement.value : undefined
        );
    }

    private load(page: number, pageSize: number, sortField: string, sortAscending: boolean, filter: string) {
        if(!this.collectionId) {
            throw Error("Collection ID needs to be set.");
        }
        this.loadingSubject.next(true);
        this.latestError = null;
        this.collectionReport = undefined;
        forkJoin(
            this.documentService.getPaginatedDocumentsByCollectionID(
                this.collectionId, page, pageSize, sortField, sortAscending, filter,
                this.truncate, this.truncateLength),
            this.iaa.getIIAReportByCollection(this.collectionId),
        ).pipe(take(1)).subscribe(([documents, reports]: [PaginatedDocuments, IAAReport[]]) => {
            this.collectionReport = reports[0];
            if(documents.meta && documents.meta.total !== undefined && documents.meta.total !== null) {
                this.length = documents.meta.total;
            }
            this.documentSubject.next(documents.documents.map((doc: Document) => {
                const docReport = this.collectionReport ? this.collectionReport.per_doc_agreement.find((d: any) => d.doc_id == doc._id) : null;
                return {
                    id: doc._id,
                    creator: this.auth.getUserDisplayName(doc.creator_id),
                    last_updated: doc._updated,
                    text_start: doc.getTextPreview(this.truncateLength),
                    annotated: doc.has_annotated && doc.has_annotated[this.auth.loggedInUser.id],
                    ann_agreement: docReport ? docReport["avg"] : null
                };
            }));
        }, (error: HttpErrorResponse) => {
            console.error(error);
            this.latestError = error.message;
            this.documentSubject.next([]);
        }, () => {
            this.loadingSubject.next(false);
        });
    }
}
