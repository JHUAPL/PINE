/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, ViewChild, ElementRef } from "@angular/core";
import { HttpErrorResponse, HttpResponse } from "@angular/common/http";
import { MatButton } from "@angular/material";

import { BackendService } from "../../service/backend/backend.service";
import { AdminService } from "../../service/admin/admin.service";
import { EventService } from "../../service/event/event.service";

import { ErrorComponent } from "../error/error.component";

@Component({
    selector: "app-admin-data",
    templateUrl: "./admin-data.component.html",
    styleUrls: ["./admin-data.component.css"]
})
export class AdminDataComponent implements OnInit {

    public static readonly SUBTITLE = "Manage System Data";

    public importDropFirst = false;

    @ViewChild("exportDownload")
    public exportDownload: ElementRef;

    @ViewChild("fileDisplay")
    public fileDisplay: ElementRef;

    public file: File;

    @ViewChild("importButton")
    public importButton: MatButton;

    public exporting = false;
    public importing = false;

    @ViewChild("exportError")
    public exportError: ErrorComponent;

    @ViewChild("importError")
    public importError: ErrorComponent;

    constructor(private admin: AdminService,
                private events: EventService) { }

    ngOnInit() {
    }

    public export() {
        this.exporting = true;
        this.exportError.clear();
        this.admin.systemExport().subscribe((response: HttpResponse<Blob>) => {
            BackendService.downloadFile(response, "export.dat", this.exportDownload.nativeElement);
            this.exporting = false;
        }, (error: HttpErrorResponse) => {
            this.exportError.showHttp(error, "exporting system data");
            this.exporting = false;
        });
    }

    public onFilesAdded(files: FileList) {
        this.file = files[0];
        this.fileDisplay.nativeElement.value = this.file ? this.file.name : "";
        this.importButton.disabled = this.file ? false : true;
    }

    public import() {
        if(!this.file) { return; } // this shouldn't happen
        this.importing = true;
        this.importError.clear();
        this.admin.systemImport(this.file, this.importDropFirst).subscribe((success: boolean) => {
            if(success) {
                this.events.systemDataImported.emit();
                this.events.showUserMessage.emit("Imported data into database.  Logging user out...");
                this.events.logout.emit();
            } else {
                this.importError.showHtml("Unknown server error (check logs).", "importing system data");
            }
            this.importing = false;
        }, (error: HttpErrorResponse) => {
            this.importError.showHttp(error, "importing system data");
            this.importing = false;
        });
    }

}
