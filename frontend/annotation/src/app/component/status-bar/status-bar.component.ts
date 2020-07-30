/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input } from "@angular/core";

@Component({
    selector: "app-status-bar",
    templateUrl: "./status-bar.component.html",
    styleUrls: ["./status-bar.component.css"]
})
export class StatusBarComponent implements OnInit {

    @Input()
    public visible = false;

    @Input()
    public message: string;

    @Input()
    public showSpinner: boolean = false;

    @Input()
    public spinnerMode: "indeterminate"|"determinate" = "indeterminate";

    @Input()
    public spinnerValue: number = 0;

    constructor() { }

    ngOnInit() {
    }

    ngAfterViewInit() {
    }
}
