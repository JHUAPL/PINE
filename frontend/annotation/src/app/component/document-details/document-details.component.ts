/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, Input, Output, EventEmitter } from "@angular/core";
import { MatDialog } from "@angular/material/dialog";

import { forkJoin } from "rxjs";
import { take } from "rxjs/operators";

import { PATHS } from "../../app.paths";

import { AuthService } from "../../service/auth/auth.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";
import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { EventService } from "../../service/event/event.service";

import { Collection, CollectionUserPermissions, newPermissions } from "../../model/collection";
import { Document } from "../../model/document";

import { ImageChooserComponent, dialog } from "../image-chooser/image-chooser.component";

@Component({
    selector: "app-document-details",
    templateUrl: "./document-details.component.html",
    styleUrls: ["./document-details.component.css"]
})
export class DocumentDetailsComponent implements OnInit {

    public readonly PATHS = PATHS;

    @Input()
    public expanded = true;

    @Input()
    public document: Document;

    @Input()
    public collection: Collection;

    public permissions: CollectionUserPermissions = newPermissions();

    @Output()
    public imageUrlChanged = new EventEmitter<string>();

    constructor(public collections: CollectionRepositoryService,
                private documents: DocumentRepositoryService,
                public auth: AuthService,
                private dialog: MatDialog,
                private event: EventService) {
    }

    ngOnInit() {
        this.documents.getCollectionUserPermissions(this.document._id).pipe(
            take(1)
        ).subscribe((permissions: CollectionUserPermissions) => {
            this.permissions = permissions;
        }, (error) => {
            console.error(error);
        });
        if(!this.collection) {
            this.collections.getCollectionDetails(this.document.collection_id)
                .pipe(take(1))
                .subscribe((collection: Collection) => {
                    this.collection = collection;
                });
        }
    }

    public updateImage() {
        if(!this.permissions.modify_document_metadata) {
            return;
        }
        dialog(this.dialog, this.collection._id, this.document.metadata ? this.document.metadata["imageUrl"] : undefined).pipe(take(1)).subscribe((result: ImageChooserComponent) => {
            if(result) {
                result.updateExistingDocument(this.document._id)
                    .pipe(take(1))
                    .subscribe(
                        (result: string) => {
                            this.event.showUserMessage.emit("Successfully updated image URL.");
                            this.imageUrlChanged.emit(result);
                        }, (error) => {
                            this.event.showUserMessage.emit("Error updating image URL: " + JSON.stringify(error));
                        }
                    );
            }
        });
    }
}
