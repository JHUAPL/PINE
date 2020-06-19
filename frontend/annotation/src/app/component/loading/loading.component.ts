/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input } from "@angular/core";

@Component({
    selector: "app-loading",
    templateUrl: "./loading.component.html",
    styleUrls: ["./loading.component.css"]
})
export class LoadingComponent implements OnInit {

    @Input()
    public loading = true;

    @Input()
    public error = false;

    @Input()
    public errorMessage: string = undefined;

    @Input()
    public spinnerColor = "accent";

    @Input()
    public spinnerMode = "indeterminate";

    constructor() { }

    ngOnInit() {
    }

    public setError(errorMessage: string) {
        this.errorMessage = errorMessage;
        this.error = true;
    }

    public clearError() {
        this.error = false;
        this.errorMessage = undefined;
    }

}
