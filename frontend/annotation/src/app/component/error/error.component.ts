/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit } from "@angular/core";
import { HttpErrorResponse } from "@angular/common/http";

@Component({
    selector: "app-error",
    templateUrl: "./error.component.html",
    styleUrls: ["./error.component.css"]
})
export class ErrorComponent implements OnInit {

    public visible = false;

    public innerHTML: string;

    constructor() { }

    ngOnInit() {
    }

    public clear() {
        this.visible = false;
        this.innerHTML = "";
    }

    public showHttp(error: HttpErrorResponse, operation: string = null) {
        console.error(error);
        if(error.status === 0) {
            this.innerHTML = "Unknown error; check console.";
        } else {
            this.innerHTML = `<span class="main">HTML Error ${error.status}</span>`;
            if(operation) {
                this.innerHTML += " " + operation;
            }
            this.innerHTML += `:<br />${error.message}`;
        }
        if(error.error && error.error._error && error.error._error.message) { // custom flask error message
            this.innerHTML += "<br />" + error.error._error.message;
        } else if(error.error && (typeof error.error === "string" || error.error instanceof String)) {
            this.innerHTML += "<br />" + error.error;
        }
        this.visible = true;
    }

    public showHtml(message: string, operation: string = null) {
        console.error(message);
        this.innerHTML = `<span class="main">Error</span>`;
        if(operation) {
            this.innerHTML += " " + operation;
        }
        this.innerHTML += `:<br />${message}`;
        this.visible = true;
    }

}
