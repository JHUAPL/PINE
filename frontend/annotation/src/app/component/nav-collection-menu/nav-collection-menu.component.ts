/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input, OnDestroy } from "@angular/core";
import * as _ from "lodash";

import { filter } from 'rxjs/operators';
import { Subscription } from 'rxjs';

import { PATHS } from "../../app.paths";

import { AnnotationService } from "../../service/annotation/annotation.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";

import { Collection } from "../../model/collection";
import { Document } from "../../model/document";
import { Annotation } from  "../../model/annotation";
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

    public readonly PATHS = PATHS;

    @Input() public collection_title: string;
    @Input() public collection_id: string;

    private _documents: DocumentMenuItem[];

    private annotationChangesSubscription : Subscription

    constructor(private documentService: DocumentRepositoryService, private annotationService: AnnotationService, private annotatedService: AnnotatedService, private auth:AuthService) { }

    ngOnInit() {
        this.listenForAnnotationChanges()
    }

    listenForAnnotationChanges() {
        this.annotationChangesSubscription = this.annotatedService.documentAnnotated.pipe(filter((newAnnotation:any)=> newAnnotation.collection_id == this.collection_id)).subscribe((newAnnotation)=>{
            if(this._documents === undefined) {
                this.refresh();
            }
            this._documents[this._documents.findIndex((document)=> document.id == newAnnotation.doc_id)].has_annotations = true
        });
    }

    public get documents() {
        if(this._documents === undefined) {
            this.refresh();
        }
        return this._documents;
    }

    public refresh() {
        this._documents = [];
        const temp = [];
        this.documentService.getDocumentsByCollectionID(this.collection_id, true).subscribe((documents: Document[]) => {
            for(const document of documents) {
                    temp.push(<DocumentMenuItem>{
                        id: document._id,
                        text_start: document.getTextPreview(),
                        has_annotations: document.has_annotated ? document.has_annotated[this.auth.loggedInUser.username] : undefined
                    });
            }
        }, (error) => {},
        () => {
            this._documents = temp;
        });
    }

    ngOnDestroy(){
        this.annotationChangesSubscription.unsubscribe()
    }

}
