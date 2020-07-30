/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Injectable } from "@angular/core";

import { StatusBarComponent } from "../../component/status-bar/status-bar.component";

@Injectable({
    providedIn: "root"
})
export class StatusBarService {

    public component: StatusBarComponent;

    constructor() { }

    public showMessage(message: string, showSpinner: boolean = false) {
        this.component.message = message;
        this.component.spinnerMode = "indeterminate";
        this.component.showSpinner = showSpinner;
        this.component.visible = true;
    }

    public showProgress(value: number) {
        this.component.spinnerMode = "determinate";
        this.component.spinnerValue = value;
        this.component.showSpinner = true;
    }

    public hideProgress() {
        this.component.showSpinner = false;
    }

    public hide() {
        this.component.visible = false;
        this.component.message = undefined;
        this.component.showSpinner = false;
        this.component.spinnerMode = "indeterminate";
    }
}
