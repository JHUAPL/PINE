import { Component, OnInit } from '@angular/core';
import { show } from "../../about/about.component";
import { MatDialog } from '@angular/material';

@Component({
    selector: 'app-toolbar-nav',
    templateUrl: './toolbar-nav.component.html',
    styleUrls: ['./toolbar-nav.component.scss']
})
export class ToolbarNavComponent implements OnInit {

    constructor(private dialog: MatDialog) { }

    ngOnInit() {
    }

    public doAbout() {
        show(this.dialog);
    }

}
