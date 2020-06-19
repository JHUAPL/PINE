/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input, Output, ElementRef, ViewChild, EventEmitter } from '@angular/core';
import { COMMA, ENTER } from '@angular/cdk/keycodes';
import { FormControl } from '@angular/forms';
import { MatAutocompleteSelectedEvent, MatChipInputEvent } from '@angular/material';

import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

@Component({
  selector: 'app-label-chooser',
  templateUrl: './label-chooser.component.html',
  styleUrls: ['./label-chooser.component.css']
})
export class LabelChooserComponent implements OnInit {

    @Input() public formFieldClass = "form-field";
    @Input() public formFieldAppearance = "standard";
    @Input() public label = "Labels";
    @Input() public selectable = true;
    @Input() public addOnBlur = true;

    @Output() public labelAdded = new EventEmitter<string>();
    @Output() public labelRemoved = new EventEmitter<string>();

    public loading = false;

    public separatorKeysCodes: number[] = [ENTER, COMMA];

    public labels: string[] = [];

    public hasError = false;
    public errorMessage: string;

    constructor() {
    }

    ngOnInit() {
    }

    public getChosenLabels() {
        return this.labels;
    }

    public showError(error: string) {
        this.errorMessage = error;
        this.hasError = true;
    }

    public clearError() {
        this.hasError = false;
        this.errorMessage = null;
    }

    add(event: MatChipInputEvent): void {
        const input = event.input;
        const value = event.value;

        // Add our label
        if((value || "").trim()) {
            const label = value.trim();
            this.labels.push(label);
            this.labelAdded.emit(label);
        }

        // Reset the input value
        if(input) {
            input.value = '';
        }
    }

    remove(label: string): void {
        const index = this.labels.indexOf(label);

        if(index >= 0) {
            const l = this.labels.splice(index, 1)[0];
            this.labelRemoved.emit(l);
        }
    }

}
