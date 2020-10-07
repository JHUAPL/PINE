/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, ElementRef, ViewChild } from "@angular/core";
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidatorFn } from "@angular/forms";
import { Router } from "@angular/router";
import { HttpEvent, HttpEventType, HttpErrorResponse } from "@angular/common/http";

import { take } from "rxjs/operators";

import * as Papa from "papaparse";

import { UserChooserComponent } from "../user-chooser/user-chooser.component";
import { LabelChooserComponent } from "../label-chooser/label-chooser.component";
import { ImageCollectionUploaderComponent } from "../image-collection-uploader/image-collection-uploader.component";

import { AppConfig } from "../../app.config";
import { AuthService } from "../../service/auth/auth.service";
import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { EventService } from "../../service/event/event.service";
import { PipelineService } from "../../service/pipeline/pipeline.service";
import { LineReader } from "../../service/utils";
import { PATHS } from "../../app.paths";

import { Collection, CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS } from "../../model/collection";
import { Pipeline } from "../../model/pipeline";
import { CreatedObject } from "../../model/created";
import { MatDialogRef } from '@angular/material';

@Component({
    selector: "app-add-collection",
    templateUrl: "./add-collection.component.html",
    styleUrls: ["./add-collection.component.css"]
})
export class AddCollectionComponent implements OnInit {

    public static readonly SUBTITLE = "Add Collection";

    public createForm: FormGroup;
    private csvFile: File;
    private pipelines: Pipeline[];
    public loading = false;
    public submitting = false;
    public submittingPercent: number = 0;
    public submitted = false;
    public hadError = false;
    public errorMessage: string;
    private manualFormError = false;
    public hasCsvFile = false;
    private csvHeader = null;
    public configAllowOverlappingNerAnnotations = true;

    @ViewChild("annotators") public annotators: UserChooserComponent;
    @ViewChild("viewers") public viewers: UserChooserComponent;
    @ViewChild("labels") public labels: LabelChooserComponent;
    @ViewChild("file") public file: ElementRef;
    @ViewChild(ImageCollectionUploaderComponent) public images: ImageCollectionUploaderComponent;

    constructor(public appConfig: AppConfig,
                private auth: AuthService,
                private collectionRepository: CollectionRepositoryService,
                private formBuilder: FormBuilder,
                private router: Router,
                private event: EventService,
                private pipeline: PipelineService,
                public dialogRef: MatDialogRef<AddCollectionComponent>) {
    }

    ngOnInit() {
        this.loading = true;
        this.createForm = this.formBuilder.group({
            creator_name: [{value: this.auth.loggedInUser.display_name, disabled: true}, Validators.required],
            creator_id: [{value: this.auth.loggedInUser.id, disabled: true}, Validators.required],
            csv_file: [{value: null, disabled: false}],
            csv_has_header: [{value: null, disabled: false}],
            csv_text_col: [{value: null, disabled: false}],
            train_every: [{value: 100, disabled: false}, [Validators.required, Validators.min(5)]],
            overlap: [{value: 0, disabled: false}, [Validators.required, Validators.max(1), Validators.min(0)]],
            pipeline_id: [{value: null, disabled: false}, Validators.required],
            classifier_parameters: [{value: null, disabled: false}, this.classifierParametersJsonValidator()],
            metadata_title: [{value: null, disabled: false}, Validators.required],
            metadata_description: [{value: null, disabled: false}, Validators.required],
            metadata_subject: [{value: null, disabled: false}],
            metadata_publisher: [{value: null, disabled: false}],
            metadata_contributor: [{value: null, disabled: false}],
            metadata_date: [{value: null, disabled: false}],
            metadata_type: [{value: null, disabled: false}],
            metadata_format: [{value: null, disabled: false}],
            metadata_identifier: [{value: null, disabled: false}],
            metadata_source: [{value: null, disabled: false}],
            metadata_language: [{value: null, disabled: false}],
            metadata_relation: [{value: null, disabled: false}],
            metadata_coverage: [{value: null, disabled: false}],
            metadata_rights: [{value: null, disabled: false}]
        });
        this.csvFile = null;
        this.pipeline.getAllPipelines().subscribe((pipelines: Pipeline[]) => {
            this.pipelines = pipelines;
            this.loading = false;
        }, (error: HttpErrorResponse) => {
            alert("Unable to load backend data (check console).");
            console.log(error.error);
        });
    }

    private classifierParametersJsonValidator(): ValidatorFn {
        return (control: AbstractControl): {[key: string]: any} | null => {
            if(!control.value) { return null; }
            try {
                const value = JSON.parse(control.value);
                if(value instanceof Object) {
                    return null;
                } else {
                    return {"invalid_json": {"error": "Needs to be object and not " + typeof(value)}};
                }
            } catch(e) {
                return {"invalid_json": {"error": e.message}};
            }
        };
    }

    public pipelineDescription(pipeline_id: string): string {
        for(const pipeline of this.pipelines) {
            if(pipeline._id === pipeline_id) {
                return pipeline.description;
            }
        }
        return null;
    }

    public handleFileInput(files: FileList) {
        this.f.csv_file.setValue(files[0].name);
        this.csvFile = files[0];
        const reader = new LineReader(this.csvFile);
        reader.read().subscribe((line: string) => {
            if(line.length > 0) {
                const results = Papa.parse(line, {header: false});
                this.csvHeader = results.data[0];
                this.f.csv_has_header.setValue(this.csvHeader.length > 1);
                this.f.csv_text_col.setValue(0);
                if(this.f.csv_has_header.value) {
                    for(let i = 0; i < this.csvHeader.length; i++) {
                        const header = this.csvHeader[i];
                        if(header.localeCompare("text") === 0) {
                            this.f.csv_text_col.setValue(i);
                            break;
                        }
                    }
                }
                this.hasCsvFile = true;
                reader.cancel();
            }
        });
    }

    public clickAddFile() {
        this.file.nativeElement.click();
    }

    // convenience getter for easy access to form fields
    get f() { return this.createForm.controls; }

    public viewersOrAnnotatorsChanged() {
        const viewers = this.viewers.getChosenUserIds();
        const annotators = this.annotators.getChosenUserIds();
        for(let i = 0; i < annotators.length; i++) {
            const annotatorId = annotators[i];
            if(viewers.indexOf(annotatorId) < 0) {
                this.annotators.setError("All annotators must also be viewers.");
                this.manualFormError = true;
                return;
            }
        }
        this.manualFormError = false;
        this.annotators.clearError();
    }

    public labelAdded() {
        this.labels.clearError();
    }

    public create() {
        this.submitted = true;

        const labels = this.labels.getChosenLabels();
        if(labels.length === 0) {
            this.labels.showError("At least one label is required.");
            return;
        } else {
            this.labels.clearError();
        }

        if(this.createForm.invalid || this.manualFormError) {
            return;
        }

        this.loading = true;

        const collection = <Collection>{};
        collection.creator_id = this.f.creator_id.value;
        collection.annotators = this.annotators.getChosenUserIds();
        collection.viewers = this.viewers.getChosenUserIds();
        collection.labels = labels;
        collection.metadata = {
            title: this.f.metadata_title.value,
            subject: this.f.metadata_subject.value,
            description: this.f.metadata_description.value,
            publisher: this.f.metadata_publisher.value,
            contributor: this.f.metadata_contributor.value,
            date: this.f.metadata_date.value,
            type: this.f.metadata_type.value,
            format: this.f.metadata_format.value,
            identifier: this.f.metadata_identifier.value,
            source: this.f.metadata_source.value,
            language: this.f.metadata_language.value,
            relation: this.f.metadata_relation.value,
            coverage: this.f.metadata_coverage.value,
            rights: this.f.metadata_rights.value
        };
        collection.archived = false;
        collection.configuration = {};
        collection.configuration[CONFIG_ALLOW_OVERLAPPING_NER_ANNOTATIONS] = this.configAllowOverlappingNerAnnotations;
        let csvTextCol = 0;
        let csvHasHeader = false;
        if(this.hasCsvFile) {
            csvHasHeader = this.f.csv_has_header.value;
            if(csvHasHeader) {
                csvTextCol = this.f.csv_text_col.value;
            }
        }
        console.log("Creating collection:");
        console.log(collection);

        this.hadError = false;
        this.errorMessage = null;
        /*
        this.collectionRepository.postCollection(collection, this.csvFile, csvTextCol, csvHasHeader, this.images.files,
                this.f.overlap.value, this.f.train_every.value, this.f.pipeline_id.value,
                JSON.parse(this.f.classifier_parameters.value)).subscribe(
            (createdCollection: Collection) => {
                const collectionId = createdCollection._id;
                this.event.showUserMessage.emit("Successfully added collection with ID " + collectionId);
                this.event.collectionAddedOrArchived.emit(createdCollection);
                this.router.navigate([PATHS.collection.details, collectionId]);
            }, (error: HttpErrorResponse) => {
                this.errorMessage = "Error: " + error.error;
                this.hadError = true;
            }
        );
        */
        this.createForm.disable();
        this.submittingPercent = 0;
        this.submitting = true;
        let subs = this.collectionRepository.postCollectionWithProgress(collection, this.csvFile, csvTextCol, csvHasHeader, this.images.files,
                this.f.overlap.value, this.f.train_every.value, this.f.pipeline_id.value, JSON.parse(this.f.classifier_parameters.value))
                    .subscribe((event: HttpEvent<CreatedObject>) => {
                        switch(event.type) {
                            case HttpEventType.UploadProgress:
                                if(event.total) {
                                    this.submittingPercent = (100 * event.loaded) / event.total;
                                }
                                break;
                            case HttpEventType.Response:
                                const collectionId = event.body._id;
                                this.collectionRepository.getCollectionDetails(collectionId).pipe(take(1)).subscribe((collection: Collection) => {
                                    this.event.showUserMessage.emit("Successfully added collection with ID " + collectionId);
                                    this.event.collectionAddedOrArchived.emit(collection);
                                    this.dialogRef.close(collection);
                                }, (error: HttpErrorResponse) => {
                                    this.errorMessage = "Error: " + error.error;
                                    this.hadError = true;
                                });
                                break;
                            default:
                                break;
                        }
                        this.loading = false;
                    }, (error: HttpErrorResponse) => {
                        this.loading = false;
                        this.errorMessage = "Error: " + error.error;
                        this.hadError = true;
                    }, () => {
                        subs.unsubscribe();
                        this.loading = false;
                        this.submitting = false;
                        this.createForm.enable();
                    });
    }

}
