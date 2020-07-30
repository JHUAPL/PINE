/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input } from "@angular/core";
import { MatDialog, MatDialogRef, MatDialogConfig } from "@angular/material";

import { take } from "rxjs/operators";

import { BackendService } from "../../service/backend/backend.service";

import { About } from "../../model/backend";
import { version } from "../../../../package.json";

export interface VersionRow {
    component: string,
    subcomponent?: string,
    version: string
}

@Component({
    selector: "app-about",
    templateUrl: "./about.component.html",
    styleUrls: ["./about.component.css"]
})
export class AboutComponent implements OnInit {

    public loading = true;

    @Input()
    public about: About;
    public version = version;
    public error = undefined;

    public tableData: VersionRow[];

    constructor(private dialogRef: MatDialogRef<AboutComponent>,
                private backend: BackendService) { }

    ngOnInit() {
        if(!this.about) {
            this.backend.about().pipe(take(1)).subscribe((about: About) => {
                this.about = about;
                this.updateTable();
            }, (error) => {
                this.error = error;
            }, () => {
                this.loading = false;
            });
        } else {
            this.updateTable();
            this.loading = false;
        }
    }

    private updateTable() {
        console.log(this.about);
        console.log(this.version);
        this.tableData = <VersionRow[]>[
            {component: "PINE", version: this.about.version},
            {component: "PINE", subcomponent: "database", version: this.about.db.version}
        ];
    }
}

export function show(dialog: MatDialog) {
    const dialogConfig = new MatDialogConfig();
    dialogConfig.disableClose = false;
    dialogConfig.autoFocus = true;
    //dialogConfig.data = data;

    const dialogRef = dialog.open(AboutComponent, dialogConfig);
    return dialogRef.afterClosed();
}
