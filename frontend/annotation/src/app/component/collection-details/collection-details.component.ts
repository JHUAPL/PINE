/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, ViewChild, AfterViewInit, Inject } from "@angular/core";
import { MatPaginator, MatTableDataSource, MatSort, MatDialog, MatDialogRef, MAT_DIALOG_DATA } from "@angular/material";
import { ActivatedRoute } from "@angular/router";
import { HttpErrorResponse } from "@angular/common/http";

import * as _ from "lodash";
import { take } from "rxjs/operators";

import { PATHS, PARAMS } from "../../app.paths";

import { AnnotationService } from "../../service/annotation/annotation.service";
import { AuthService } from "../../service/auth/auth.service";
import { BackendService } from "../../service/backend/backend.service"
import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";
import { EventService } from "../../service/event/event.service";
import { PipelineService } from "../../service/pipeline/pipeline.service";
import { MetricsService } from "../../service/metrics/metrics.service";

import { Annotation } from  "../../model/annotation";
import { Document } from "../../model/document";
import { Classifier } from "../../model/classifier";
import { Collection, DownloadCollectionData, METADATA_TITLE } from "../../model/collection";
import { Pipeline } from "../../model/pipeline";
import {DocumentMenuItem} from "../nav-collection-menu/nav-collection-menu.component";
import { Metric } from "../../model/metrics";
import { IaaReportingService } from '../../service/iaa-reporting/iaa-reporting.service';
import { IAAReport } from '../../model/iaareport';
import { DownloadCollectionDataDialogComponent } from '../download-collection-data.dialog/download-collection-data.dialog.component';
import { ImageCollectionUploaderComponent, dialog } from "../image-collection-uploader/image-collection-uploader.component";

export interface AnnotatorDialogData {
  annotator: string;
}

export interface ViewerDialogData {
  viewer: string;
}

export interface LabelDialogData {
  label: string;
}

export interface DocumentRow {
    id: string;
    creator: string;
    last_updated: Date;
    text_start: string;
    annotated: boolean;
    ann_agreement: number
}

@Component({
    selector: "app-collection-details",
    templateUrl: "./collection-details.component.html",
    styleUrls: ["./collection-details.component.css"]
})
export class CollectionDetailsComponent implements OnInit {

    public static readonly SUBTITLE = "Collection Details";

    public readonly PATHS = PATHS;

    public loading = false;
    public canArchive = false;

    displayedColumns: string[] = ["id", "creator", "last_updated", "text_start", "annotated", "agreement"];
    collection: Collection;
    public classifier: Classifier;
    public pipeline: Pipeline;
    documents: DocumentRow[];
    dataSource = new MatTableDataSource<DocumentRow>();
    nextDocId: string = null;
    metrics: object;
    iaa_report : IAAReport;
    private new_annotator: string = null;
    private new_viewer: string = null;
    private new_label: string = null;
    public can_add_users: boolean = false;
    public can_add_documents: boolean = false;
    public can_add_images: boolean = false;


    @ViewChild(MatPaginator) paginator: MatPaginator;
    @ViewChild(MatSort) sort: MatSort;

    constructor(private route: ActivatedRoute,
                private annotationService: AnnotationService,
                private collectionService: CollectionRepositoryService,
                private documentsService: DocumentRepositoryService,
                private pipelineService: PipelineService,
                private metricsService: MetricsService,
                private events: EventService,
                public auth: AuthService,
                private iaa_reports : IaaReportingService,
                private dialog: MatDialog) {
        this.can_add_images = this.can_add_documents = false;
    }

    ngOnInit() {
        this.loading = true;
        this.dataSource.paginator = this.paginator;
        this.route.paramMap.subscribe(params => {
            const colId = params.get(PARAMS.collection.details.collection_id);
            this.collectionService.getCanAddDocumentsOrImages(colId).pipe(take(1)).subscribe((val: boolean) => {
                this.can_add_images = this.can_add_documents = val;
            }, (error) => {
                console.error(error);
            });
            const tempDocuments = [];
            this.collectionService.getCollectionDetails(colId).subscribe((collection: Collection) => {
                this.collection = collection;
                this.can_add_users = collection.creator_id === this.auth.loggedInUser.id;
                this.canArchive = true;//collection.creator_id === this.auth.getLocalLoggedInUser().id;
                if(this.documents) {
                    this.documents.length = 0;
                }
                this.iaa_reports.getIIAReportByCollection(colId).subscribe((iaa_report: any)=>{
                    this.iaa_report = iaa_report[0]
                })
                this.documentsService.getDocumentsByCollectionIDPaginated(colId, true).subscribe((document: Document) => {
                      tempDocuments.push(<DocumentRow>{
                        id: document._id,
                        creator: this.auth.getUserDisplayName(document.creator_id),
                        last_updated: document._updated,
                        text_start: document.getTextPreview(),
                        annotated: document.has_annotated ? document.has_annotated[this.auth.loggedInUser.id] : undefined,
                        ann_agreement: this.iaa_report ? this.iaa_report.per_doc_agreement[this.iaa_report.per_doc_agreement.findIndex((doc: any)=> doc.doc_id == document._id)]["avg"] : null
                      });
                }, (error) => {},
                () => {
                    this.documents = tempDocuments;
                    this.dataSource.data = this.documents;
                    this.dataSource.sort = this.sort
                    this.pipelineService.getClassifierForCollection(colId).subscribe((classifier: Classifier) => {
                        this.classifier = classifier;
                        this.nextDocId = null;
                        this.metricsService.getMetricForClassifier(this.classifier._id).toPromise().then((metrics)=>{
                            this.metrics = metrics
                        })
                        this.pipelineService.getPipeline(classifier.pipeline_id).subscribe((pipeline: Pipeline) => {
                            this.pipeline = pipeline;
                            this.pipelineService.getNextDocumentIdForClassifier(classifier._id).subscribe((docId: string) => {
                                this.nextDocId = docId;
                                this.loading = false;
                            }, (error: HttpErrorResponse) => {
                                console.error("Error getting next document ID for collection", error);
                                this.loading = false;
                            },
                            () => {
                              // this.metricsService.getMetricForClassifier()
                          }
                            );
                        });
                    }, (error) => {
                        console.error("Error getting classifier for collection", error);
                        this.classifier = null;
                        this.nextDocId = null;
                        this.loading = false;
                    });
                });
                
            });
        });
    }
    
    public getAdditionalMetadata() {
        const additional = {};
        for(const key in this.collection.metadata) {
            if(key.toLowerCase() !== METADATA_TITLE && this.collection.metadata[key]) {
                additional[key] = this.collection.metadata[key];
            }
        }
        return additional;
    }

    applyFilter(filterValue: string) {
        this.dataSource.filter = filterValue.trim().toLowerCase();
    }

    public archiveCollection() {
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
        dialog(this.dialog)
            .pipe(take(1))
            .subscribe((uploader: ImageCollectionUploaderComponent) => {
                if(uploader) {
                    uploader.upload(this.collection._id, true)
                        .pipe(take(1))
                        .subscribe(_ => {},
                            (error) => {
                                console.error(error);
                                this.events.showUserMessage.emit("Unable to upload images.");
                            });
                }
            });
    }

    public openAddAnnotatorDialog() {
    const dialogRef = this.dialog.open(AddAnnotatorDialog, {
      width: '250px',
      data: {new_annotator: this.new_annotator}
    });

    dialogRef.afterClosed().subscribe(result => {
      this.new_annotator = result;
      if(this.new_annotator){
        this.new_annotator = this.new_annotator.replace(/[|&;$%@"<>()+,]/g, "");
        this.collectionService.addAnnotatorToCollection(this.collection._id, this.new_annotator).subscribe(res => {;
          this.events.showUserMessage.emit("New Annotator Added to Collection");
          this.collection.annotators.push(this.new_annotator);
          if (!this.collection.viewers.includes(this.new_annotator)){
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
    const dialogRef = this.dialog.open(AddViewerDialog, {
      width: '250px',
      data: {new_viewer: this.new_viewer}
    });

    dialogRef.afterClosed().subscribe(result => {
      this.new_viewer = result;
      if(this.new_viewer){
        this.new_viewer = this.new_viewer.replace(/[|&;$%@"<>()+,]/g, "");
        this.collectionService.addViewerToCollection(this.collection._id, this.new_viewer).subscribe(res => {;
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
    const dialogRef = this.dialog.open(AddLabelDialog, {
      width: '250px',
      data: {new_label: this.new_label}
    });

    dialogRef.afterClosed().subscribe(result => {
      this.new_label = result;
      if(this.new_label){
        this.new_label = this.new_label.replace(/[|&;$%@"<>()+,]/g, "");
        this.collectionService.addLabelToCollection(this.collection._id, this.new_label).subscribe(res => {;
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
        DownloadCollectionDataDialogComponent.show(this.dialog, this.collection).subscribe(
            (value: DownloadCollectionData) => {
                if(value) {
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
    @Inject(MAT_DIALOG_DATA) public data: AnnotatorDialogData) {}

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
    @Inject(MAT_DIALOG_DATA) public data: ViewerDialogData) {}

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
    @Inject(MAT_DIALOG_DATA) public data: LabelDialogData) {}

  onNoClick() {
    this.dialogRef.close();
  }

}
