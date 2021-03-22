/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input, ViewChild, Inject } from "@angular/core";
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { FormBuilder, FormGroup, Validators, ValidatorFn, AbstractControl } from "@angular/forms";
import { HttpErrorResponse } from "@angular/common/http";

import { Observable } from "rxjs";
import { take } from "rxjs/operators";

import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";
import { uuidv4 } from "../util";

import { CollectionUserPermissions, newPermissions } from "../../model/collection";
import { Document } from "../../model/document";

@Component({
    selector: "app-image-chooser",
    templateUrl: "./image-chooser.component.html",
    styleUrls: ["./image-chooser.component.css"]
})
export class ImageChooserComponent implements OnInit {

    @Input()
    public collectionId: string;

    @Input()
    public startingUrl: string;

    public readonly uuidv4 = uuidv4();

    public permissions: CollectionUserPermissions = newPermissions();
    public form: FormGroup;
    public existingCollectionImageUrl: string;
    private file: File;

    constructor(private fb: FormBuilder,
                private collections: CollectionRepositoryService,
                private documents: DocumentRepositoryService) {
        this.form = this.fb.group({
            type: ["none", [Validators.required]],
            url: [],
            file_display: [],
            file_path: [],
        });
    }

    ngOnInit() {
        this.collections.getUserPermissions(this.collectionId).pipe(
            take(1)
        ).subscribe((permissions: CollectionUserPermissions) => {
            this.permissions = permissions;
        }, (error) => {
            console.error(error);
        });
        if(this.startingUrl) {
            this.f.type.setValue("url");
            this.f.url.setValue(this.startingUrl);
        }
        setTimeout(() => {
            // for some reason these validators only work this way
            this.f.url.setValidators([
                this.makeImageFieldValidator("url"),
                this.makeImagePathValidator("url")
            ]);
            this.f.url.updateValueAndValidity();
            this.f.file_display.setValidators([
                this.makeImageFieldValidator("file")
            ]);
            this.f.file_display.updateValueAndValidity();
            this.f.file_path.setValidators([
                this.makeImagePathValidator("file")
            ]);
            this.f.file_path.updateValueAndValidity();
        })
        this.f.type.valueChanges.subscribe((_) => {
            this.f.url.updateValueAndValidity();
            this.f.file_display.updateValueAndValidity();
            this.f.file_path.updateValueAndValidity();
            this.existingCollectionImageUrl = undefined;
        });
        this.f.url.valueChanges.subscribe((value: string) => {
            if(value && this.f.url.valid && this.f.type.value == "url") {
                if(value.startsWith("/")) {
                    this.updateExistingCollectionImageUrl(value);
                }
            }
        });
        this.f.file_path.valueChanges.subscribe((value: string) => {
            if(value && this.f.file_path.valid && this.f.type.value == "file") {
                this.updateExistingCollectionImageUrl(value);
            }
        });
    }

    private updateExistingCollectionImageUrl(value: string) {
        this.existingCollectionImageUrl = undefined;
        if(!value) return;
        if(value.startsWith("/")) { // this will error out and will get removed by backend anyway
            value = value.substring(1);
        }
        if(value.length == 0) return;
        this.collections.getCollectionImageExists(this.collectionId, value)
            .pipe(take(1))
            .subscribe((exists: boolean) => {
                if(exists) {
                    this.existingCollectionImageUrl = this.collections.collectionImageUrl(this.collectionId, "/" + value);
                }
            }, (_: HttpErrorResponse) => {
                //console.error(error);
            });
    }

    private makeImageFieldValidator(image_type: string): ValidatorFn {
        return (control: AbstractControl) => {
            return (this.form && this.f.type.value == image_type) ? Validators.required(control) : null;
        }
    }

    private makeImagePathValidator(image_type: string): ValidatorFn {
        return (control: AbstractControl) => {
            if(!this.f.type || this.f.type.value !== image_type) return null;
            return control && control.value && control.value.replace(/\//g, "").length == 0 ? {"invalidValue": true} : null;
        }
    }

    public fileAdded(files: FileList) {
        if(files.length > 0) {
            this.file = files[0];
            this.f.file_display.setValue(this.file.name);
            this.f.file_path.setValue(this.file.name);
        } else {
            this.file = undefined;
            this.f.file_display.setValue(undefined);
            this.f.file_path.setValue(undefined);
        }
        this.f.file_display.markAsTouched();
        this.f.file_display.updateValueAndValidity();
        this.f.file_path.markAsTouched();
        this.f.file_path.updateValueAndValidity();
    }

    public get f() {
        return this.form.controls;
    }

    public markAsTouched() {
        for(let k in this.f) {
            this.f[k].markAsTouched();
        }
    }

    public get valid(): boolean {
        return this.form.valid;
    }

    public get imageType(): "url" | "file" | "none" {
        return this.form.value.type;
    }

    public get imageUrl(): string {
        let val = this.form.value;
        if(val.type === "url") {
            return val.url;
        } else if(val.type === "file") {
            let url: string = val.file_path;
            if(!url) {
                url = val.file_display;
            }
            while(url.startsWith("/")) {
                url = url.substring(1);
            }
            return "/" + url;
        } else {
            return null;
        }
    }

    public get imageFile(): File {
        return this.form.value.type === "file" ? this.file : undefined;
    }

    public get imagePath(): string {
        let path = this.imageUrl;
        if(path.startsWith("/")) {
            path = path.substring(1);
        }
        return path;
    }

    public updateDocumentBeingCreated(document: Document): Observable<boolean> {
        return new Observable<boolean>((observer) => {
            if(this.imageType === "file") {
                this.collections.uploadCollectionImage(this.collectionId, this.imagePath, this.imageFile)
                    .pipe(take(1)).subscribe((imageUrl: string) => {
                        if(!document.metadata) {
                            document.metadata = {};
                        }
                        document.metadata["imageUrl"] = imageUrl;
                        observer.next(true);
                    }, (error) => {
                        observer.error(error);
                    }, () => {
                        observer.complete();
                    });
            } else if(this.imageType === "url") {
                if(!document.metadata) {
                    document.metadata = {};
                }
                document.metadata["imageUrl"] = this.imageUrl;
                observer.next(true);
                observer.complete();
            } else {
                observer.next(false);
                observer.complete();
            }
        });
    }

    public updateExistingDocument(documentId: string): Observable<string> {
        return new Observable<string>((observer) => {
            const updateMetadata = (imageUrl: string) => {
                this.documents.updateMetadata(documentId, {imageUrl})
                    .pipe(take(1))
                    .subscribe(
                        _ => observer.next(imageUrl),
                        error => observer.error(error),
                        () => observer.complete());
            };

            if(this.imageType == "file") {
                this.collections.uploadCollectionImage(this.collectionId, this.imagePath, this.imageFile)
                    .pipe(take(1))
                    .subscribe(
                        (imageUrl: string) => {
                            updateMetadata(imageUrl);
                        }, (error) => {
                            observer.error(error);
                            observer.complete();
                        }
                    );
            } else {
                updateMetadata(this.imageUrl);
            }
        });
    }
}

interface ImageChooserDialogData {
    collectionId: string;
    startingUrl: string;
}

@Component({
    selector: "app-image-dialog",
    templateUrl: "./image-chooser.dialog.html",
    styleUrls: ["./image-chooser.dialog.css"]
})
export class ImageChooserDialog implements OnInit {

    @ViewChild(ImageChooserComponent)
    public chooser: ImageChooserComponent;

    constructor(public dialogRef: MatDialogRef<ImageChooserDialog>,
                @Inject(MAT_DIALOG_DATA) public data: ImageChooserDialogData) {
    }

    ngOnInit() { }

    public closeDialog(andSave: boolean) {
        if(andSave && !this.chooser.valid) {
            this.chooser.markAsTouched();
            return;
        }
        this.dialogRef.close(andSave ? this.chooser : undefined);
    }
}

export function dialog(dialog: MatDialog, collectionId: string, startingUrl: string): Observable<ImageChooserComponent> {
    let dialogRef = dialog.open(ImageChooserDialog, {
        data: <ImageChooserDialogData>{
            collectionId,
            startingUrl
        }
    });
    return dialogRef.afterClosed();
}
