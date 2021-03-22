/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, ViewChild, AfterViewInit, Inject, OnDestroy, ElementRef } from "@angular/core";
import { KeyValue } from "@angular/common";
import { MatPaginator, MatSort, MatDialog, MatDialogRef, MAT_DIALOG_DATA } from "@angular/material";
import { ActivatedRoute, Router } from "@angular/router";
import { HttpErrorResponse } from "@angular/common/http";

import { forkJoin, BehaviorSubject } from "rxjs";
import { filter, take } from "rxjs/operators";

import * as _ from "lodash";

import { PATHS, PARAMS } from "../../app.paths";

import { AuthService } from "../../service/auth/auth.service";
import { BackendService } from "../../service/backend/backend.service"
import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";
import { EventService } from "../../service/event/event.service";
import { PipelineService } from "../../service/pipeline/pipeline.service";
import { MetricsService } from "../../service/metrics/metrics.service";

import { Classifier } from "../../model/classifier";
import { Collection, CollectionUserPermissions, DownloadCollectionData, METADATA_TITLE, newPermissions, PERMISSION_TITLES } from "../../model/collection";
import { Pipeline } from "../../model/pipeline";
import { Metric } from "../../model/metrics";
import { IaaReportingService } from '../../service/iaa-reporting/iaa-reporting.service';
import { IAAReport } from '../../model/iaareport';
import { DownloadCollectionDataDialogComponent } from '../download-collection-data.dialog/download-collection-data.dialog.component';
import { ImageCollectionUploaderComponent, dialog } from "../image-collection-uploader/image-collection-uploader.component";
import { AddDocumentComponent, AddDocumentDialogData } from '../add-document/add-document.component';

import { DocumentDataSource } from "./document-data-source";

export interface AnnotatorDialogData {
    annotator: string;
}

export interface ViewerDialogData {
    viewer: string;
}

export interface LabelDialogData {
    label: string;
}

@Component({
    selector: "app-collection-details",
    templateUrl: "./collection-details.component.html",
    styleUrls: ["./collection-details.component.css"]
})
export class CollectionDetailsComponent implements OnInit, AfterViewInit, OnDestroy {

    public static readonly SUBTITLE = "Collection Details";

    public readonly PATHS = PATHS;
    public readonly PERMISSION_TITLES = PERMISSION_TITLES;

    public tabIndex: number = 0;

    public loading = false;

    displayedColumns: string[] = ["id", "creator", "last_updated", "text_start", "annotated", "agreement"];
    collection: Collection;
    public classifier: Classifier;
    public pipeline: Pipeline;
    public documents: DocumentDataSource;
    nextDocId: string = null;
    metrics: object;
    iaa_report: IAAReport;
    private new_annotator: string = null;
    private new_viewer: string = null;
    private new_label: string = null;
    public permissions: CollectionUserPermissions = newPermissions();

    @ViewChild(MatPaginator) public paginator: MatPaginator;
    @ViewChild(MatSort) public sort: MatSort;
    @ViewChild("filter") public filter: ElementRef;
    private tableReady = new BehaviorSubject<boolean>(false);

    constructor(private router: Router,
        private route: ActivatedRoute,
        private collectionService: CollectionRepositoryService,
        private documentsService: DocumentRepositoryService,
        private pipelineService: PipelineService,
        private metricsService: MetricsService,
        private events: EventService,
        public auth: AuthService,
        private iaa_reports: IaaReportingService,
        private dialog: MatDialog) {
    }

    ngOnInit() {
        this.loading = true;
        this.documents = new DocumentDataSource(this.documentsService, this.auth, this.iaa_reports);

        this.route.queryParams.subscribe(params => {
            if(params.tab != undefined) {
                this.tabIndex = params.tab;
            }
        });
        this.route.paramMap.subscribe(params => {
            this.loadCollection(params.get(PARAMS.collection.details.collection_id));
        });
        
    }

    ngAfterViewInit() {
        this.tableReady.next(true);
    }

    ngOnDestroy() {
        this.documents.ngOnDestroy();
    }

    private loadCollection(collectionId: string) {
        this.loading = true;
        forkJoin(
            this.documents.setCollection(collectionId),
            this.collectionService.getUserPermissions(collectionId),
            this.collectionService.getCollectionDetails(collectionId),
            this.pipelineService.getClassifierForCollection(collectionId),
        ).pipe(
            take(1)
        ).subscribe(([_, permissions, collection, classifier]: [boolean, CollectionUserPermissions, Collection, Classifier]) => {
            this.tableReady.asObservable().pipe(
                filter(ready => ready),
                take(1)
            ).subscribe((_) => {
                this.documents.setPaginatorSortAndFilter(this.paginator, this.sort, this.filter);
            });
            this.permissions = permissions;
            this.collection = collection;
            this.classifier = classifier;

            this.nextDocId = null;
            this.pipeline = null;
            forkJoin(
                this.metricsService.getMetricForClassifier(this.classifier._id),
                this.pipelineService.getPipeline(this.classifier.pipeline_id),
                this.pipelineService.getNextDocumentIdForClassifier(this.classifier._id)
            ).pipe(take(1)).subscribe((results: [Metric, Pipeline, string]) => {
                this.metrics = results[0];
                this.pipeline = results[1];
                this.nextDocId = results[2];
            }, (error) => {
                console.error("Error loading classifier data.", error);
                this.classifier = null;
                this.nextDocId = null;
            }, () => {
                this.loading = false;
            });
        }, (error) => {
            console.error("Error loading collection data.", error);
            this.classifier = null;
            this.nextDocId = null;
            this.loading = false;
        });
    }

    public updateTabInUrl() {
        let param = { tab: this.tabIndex };
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: param,
            queryParamsHandling: 'merge'
        });
    }

    public permissionTooltip(permission: boolean, action: string = "do this action on") {
        return permission ? undefined : `You do not have permission to ${action} this collection.`;
    }
    
    public permissionSorter(a: KeyValue<string, boolean>, b: KeyValue<string, boolean>): number {
        return PERMISSION_TITLES[a.key].localeCompare(PERMISSION_TITLES[b.key]);
    }

    public addDocument() {
        if (this.collection && this.permissions.add_documents) {
            let dialogData: AddDocumentDialogData = {
                collection: this.collection
            };
            const dialogRef = this.dialog.open(AddDocumentComponent, {
                width: '550px',
                data: dialogData
            });
        }
    }

    public backToCollectionList() {
        this.router.navigate(['collections']);
    }

    public getAdditionalMetadata() {
        const additional = {};
        for (const key in this.collection.metadata) {
            if (key.toLowerCase() !== METADATA_TITLE && this.collection.metadata[key]) {
                additional[key] = this.collection.metadata[key];
            }
        }
        return additional;
    }

    public archiveCollection() {
        if(!this.permissions.archive) {
            return;
        }
        this.collectionService.archiveCollection(this.collection._id).subscribe((collection: Collection) => {
            this.collection = collection;
            this.events.collectionAddedOrArchived.emit(collection);
            this.events.showUserMessage.emit("Collection successfully archived.");
        }, (error: HttpErrorResponse) => {
            this.events.showUserMessage.emit("ERROR: Collection was not successfully archived:\n" +
                `Error ${error.status}: ${error.message}`);
        });
    }

    public unarchiveCollection() {
        if(!this.permissions.archive) {
            return;
        }
        this.collectionService.unarchiveCollection(this.collection._id).subscribe((collection: Collection) => {
            this.collection = collection;
            this.events.collectionAddedOrArchived.emit(collection);
            this.events.showUserMessage.emit("Collection successfully unarchived.");
        }, (error: HttpErrorResponse) => {
            this.events.showUserMessage.emit("ERROR: Collection was not successfully unarchived:\n" +
                `Error ${error.status}: ${error.message}`);
        });
    }

    public uploadImages() {
        if(!this.permissions.add_images) {
            return;
        }
        dialog(this.dialog)
            .pipe(take(1))
            .subscribe((uploader: ImageCollectionUploaderComponent) => {
                if (uploader) {
                    uploader.upload(this.collection._id, true)
                        .pipe(take(1))
                        .subscribe(_ => { },
                            (error) => {
                                console.error(error);
                                this.events.showUserMessage.emit("Unable to upload images.");
                            });
                }
            });
    }

    public openAddAnnotatorDialog() {
        if(!this.permissions.modify_users) {
            return;
        }

        const dialogRef = this.dialog.open(AddAnnotatorDialog, {
            width: '250px',
            data: { new_annotator: this.new_annotator }
        });

        dialogRef.afterClosed().subscribe(result => {
            this.new_annotator = result;
            if (this.new_annotator) {
                this.new_annotator = this.new_annotator.replace(/[|&;$%@"<>()+,]/g, "");
                this.collectionService.addAnnotatorToCollection(this.collection._id, this.new_annotator).subscribe(res => {
                    ;
                    this.events.showUserMessage.emit("New Annotator Added to Collection");
                    this.collection.annotators.push(this.new_annotator);
                    if (!this.collection.viewers.includes(this.new_annotator)) {
                        this.collection.viewers.push(this.new_annotator);
                    }
                }, (error: HttpErrorResponse) => {
                    this.events.showUserMessage.emit("ERROR: Annotator was not successfully added:\n" +
                        `Error ${error.status}: ${error.message}`);
                });
            }
        });
    }

    public openAddViewerDialog() {
        if(!this.permissions.modify_users) {
            return;
        }

        const dialogRef = this.dialog.open(AddViewerDialog, {
            width: '250px',
            data: { new_viewer: this.new_viewer }
        });

        dialogRef.afterClosed().subscribe(result => {
            this.new_viewer = result;
            if (this.new_viewer) {
                this.new_viewer = this.new_viewer.replace(/[|&;$%@"<>()+,]/g, "");
                this.collectionService.addViewerToCollection(this.collection._id, this.new_viewer).subscribe(res => {
                    ;
                    this.events.showUserMessage.emit("New Viewer Added to Collection");
                    this.collection.viewers.push(this.new_viewer);
                }, (error: HttpErrorResponse) => {
                    this.events.showUserMessage.emit("ERROR: Viewer was not successfully added:\n" +
                        `Error ${error.status}: ${error.message}`);
                });
            }
        });
    }

    public openAddLabelDialog() {
        if(!this.permissions.modify_labels) {
            return;
        }

        const dialogRef = this.dialog.open(AddLabelDialog, {
            width: '250px',
            data: { new_label: this.new_label }
        });

        dialogRef.afterClosed().subscribe(result => {
            this.new_label = result;
            if (this.new_label) {
                this.new_label = this.new_label.replace(/[|&;$%@"<>()+,]/g, "");
                this.collectionService.addLabelToCollection(this.collection._id, this.new_label).subscribe(res => {
                    ;
                    this.events.showUserMessage.emit("New Label Added to Collection");
                    this.collection.labels.push(this.new_label);
                }, (error: HttpErrorResponse) => {
                    this.events.showUserMessage.emit("ERROR: Label was not successfully added:\n" +
                        `Error ${error.status}: ${error.message}`);
                });
            }
        });
    }

    public downloadData() {
        if(!this.permissions.download_data) {
            return;
        }

        DownloadCollectionDataDialogComponent.show(this.dialog, this.collection).subscribe(
            (value: DownloadCollectionData) => {
                if (value) {
                    this.collectionService.downloadData(this.collection._id, value).subscribe(
                        (response) => {
                            BackendService.downloadFile(response, "collection_" + this.collection._id + ".json");
                        }, (error: HttpErrorResponse) => {
                            this.events.showUserMessage.emit("ERROR: Collection data was not successfully downloaded:\n" +
                                `Error ${error.status}: ${error.message}`);
                        }
                    );
                }
            });
    }
}

@Component({
    selector: 'add-annotator-dialog',
    templateUrl: './collection-details-add-annotator-modal.component.html',
})
export class AddAnnotatorDialog {

    constructor(
        public dialogRef: MatDialogRef<AddAnnotatorDialog>,
        @Inject(MAT_DIALOG_DATA) public data: AnnotatorDialogData) { }

    onNoClick() {
        this.dialogRef.close();
    }

}

@Component({
    selector: 'add-viewer-dialog',
    templateUrl: './collection-details-add-viewer-modal.component.html',
})
export class AddViewerDialog {

    constructor(
        public dialogRef: MatDialogRef<AddViewerDialog>,
        @Inject(MAT_DIALOG_DATA) public data: ViewerDialogData) { }

    onNoClick() {
        this.dialogRef.close();
    }

}

@Component({
    selector: 'add-label-dialog',
    templateUrl: './collection-details-add-label-modal.component.html',
})
export class AddLabelDialog {

    constructor(
        public dialogRef: MatDialogRef<AddLabelDialog>,
        @Inject(MAT_DIALOG_DATA) public data: LabelDialogData) { }

    onNoClick() {
        this.dialogRef.close();
    }

}
