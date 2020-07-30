/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input, OnDestroy } from "@angular/core";
import * as _ from "lodash";

import { Observable, Subscription, of } from 'rxjs';
import { filter, map, tap, take } from 'rxjs/operators';

import { PATHS } from "../../app.paths";

import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";

import { Document } from "../../model/document";
import { AnnotatedService } from 'src/app/service/annotated/annotated.service';
import { AuthService } from 'src/app/service/auth/auth.service';

export interface DocumentMenuItem {
    id: string;
    text_start: string;
    has_annotations: boolean
};

@Component({
    selector: "app-nav-collection-menu",
    templateUrl: "./nav-collection-menu.component.html",
    styleUrls: ["./nav-collection-menu.component.css"]
})
export class NavCollectionMenuComponent implements OnInit, OnDestroy {

    @Input() public collection_title: string;
    @Input() public collection_id: string;

    public readonly PATHS = PATHS;
    public loading = true;

    private _documents: DocumentMenuItem[];

    private annotationChangesSubscription : Subscription;

    constructor(private documentService: DocumentRepositoryService,
                private annotatedService: AnnotatedService,
                private auth :AuthService) { }

    ngOnInit() {
        this.listenForAnnotationChanges();
    }

    listenForAnnotationChanges() {
        this.annotationChangesSubscription = this.annotatedService.documentAnnotated.pipe(
            filter((newAnnotation:any)=> newAnnotation.collection_id == this.collection_id))
            .subscribe((newAnnotation)=> {
                this.documents$.pipe(take(1)).subscribe((documents: DocumentMenuItem[]) => {
                    documents.find(doc => doc.id == newAnnotation.doc_id).has_annotations = true;
                });
            });
    }

    public get documents(): DocumentMenuItem[] {
        if(this._documents === undefined) {
            this.reloadAsync();
        }
        return this._documents;
    }

    public get documents$(): Observable<DocumentMenuItem[]> {
        if(this._documents !== undefined) {
            return of(this._documents);
        } else {
            return this.reload();
        }
    }

    public reloadAsync() {
        this.reload().pipe(take(1)).subscribe();
    }

    public reload(): Observable<DocumentMenuItem[]> {
        this.loading = true;
        return this.documentService.getDocumentsByCollectionID(this.collection_id, true).pipe(
            map((documents: Document[]) => documents.map(doc => <DocumentMenuItem>{
                    id: doc._id,
                    text_start: doc.getTextPreview(),
                    has_annotations: doc.has_annotated ? doc.has_annotated[this.auth.loggedInUser.id] : undefined
                })),
            tap((documents: DocumentMenuItem[]) => {
                this._documents = documents;
                this.loading = false;
            }));
    }

    ngOnDestroy(){
        this.annotationChangesSubscription.unsubscribe();
    }

}
