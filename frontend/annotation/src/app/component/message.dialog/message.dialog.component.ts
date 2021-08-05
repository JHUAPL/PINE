/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Inject } from "@angular/core";
import { MatDialog, MatDialogConfig, MAT_DIALOG_DATA } from "@angular/material/dialog";

import { Observable } from "rxjs";

export interface MessageDialogAction {
    value: any;
    display: string;
}

export interface MessageDialogData {
    title: string;
    message: string;
    actions: MessageDialogAction[];
}

@Component({
    selector: "app-message.dialog",
    templateUrl: "./message.dialog.component.html",
    styleUrls: ["./message.dialog.component.css"]
})
export class MessageDialogComponent implements OnInit {

    constructor(@Inject(MAT_DIALOG_DATA) public data: MessageDialogData) {
    }

    ngOnInit() {
    }

}

export function show(dialog: MatDialog, data: MessageDialogData): Observable<any> {
    const dialogConfig = new MatDialogConfig();
    dialogConfig.disableClose = true;
    dialogConfig.autoFocus = true;
    dialogConfig.data = data;

    const dialogRef = dialog.open(MessageDialogComponent, dialogConfig);
    return dialogRef.afterClosed();
}

export function confirm(dialog: MatDialog, title: string, message: string): Observable<boolean> {
    const actions = <MessageDialogAction[]>[];
    actions.push(<MessageDialogAction>{
        value: true,
        display: "Yes"
    });
    actions.push(<MessageDialogAction>{
        value: false,
        display: "No"
    });
    const data = <MessageDialogData>{
        title: title,
        message: message,
        actions: actions
    };
    return show(dialog, data);
}
