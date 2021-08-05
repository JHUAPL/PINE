/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Inject } from '@angular/core';
import { MatDialog, MatDialogConfig, MatDialogRef, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { FormBuilder, FormGroup, FormControl } from "@angular/forms";

import { Collection, DownloadCollectionData } from "../../model/collection";

@Component({
    selector: 'app-download-collection-data.dialog',
    templateUrl: './download-collection-data.dialog.component.html',
    styleUrls: ['./download-collection-data.dialog.component.css']
})
export class DownloadCollectionDataDialogComponent implements OnInit {

    public form: FormGroup;

    constructor(
        private dialogRef: MatDialogRef<DownloadCollectionDataDialogComponent>,
        private fb: FormBuilder,
        @Inject(MAT_DIALOG_DATA) public collection: Collection) {
        this.form = new FormGroup({
            include_collection_metadata: new FormControl(true),
            include_document_metadata: new FormControl(true),
            include_document_text: new FormControl(true),
            include_annotations: new FormControl(true),
            include_annotation_latest_version_only: new FormControl(true)
        });
    }

    ngOnInit() {
    }
    
    public download() {
        let data = this.form.value;
        this.dialogRef.close(<DownloadCollectionData>data);
    }
    
    public cancel() {
        this.dialogRef.close(null);
    }

    public static show(dialog: MatDialog, collection: Collection) {
        const dialogConfig = new MatDialogConfig();
        dialogConfig.disableClose = true;
        dialogConfig.autoFocus = true;
        dialogConfig.data = collection;

        const dialogRef = dialog.open(DownloadCollectionDataDialogComponent, dialogConfig);
        return dialogRef.afterClosed();
    }

}
