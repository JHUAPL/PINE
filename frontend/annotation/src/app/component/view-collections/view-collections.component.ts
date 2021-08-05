/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ViewChild } from "@angular/core";
import { MatDialog } from "@angular/material/dialog";
import { MatPaginator } from "@angular/material/paginator";
import { MatTableDataSource } from "@angular/material/table";

import { PATHS } from "../../app.paths";
import { AppConfig } from "../../app.config";

import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { AuthService } from "../../service/auth/auth.service";

import { Collection } from "../../model/collection";
import { AddCollectionComponent } from '../add-collection/add-collection.component';

export interface CollectionRow {
    id: string;
    title: string;
    creator: string;
    last_updated: Date;
}

@Component({
    selector: "app-view-collections",
    templateUrl: "./view-collections.component.html",
    styleUrls: ["./view-collections.component.css"],
})
export class ViewCollectionsComponent implements OnInit {

    public static readonly SUBTITLE = "View Collections";

    public readonly PATHS = PATHS;

    public loading: boolean;
    public error: string;

    public active = true;

    collections: CollectionRow[] = [];
    selected = null;

    displayedColumns: string[] = ["title", "creator", "last_updated"];
    dataSource = new MatTableDataSource<CollectionRow>(this.collections);

    @ViewChild(MatPaginator)
    paginator: MatPaginator;

    constructor(public collectionsService: CollectionRepositoryService,
                public appConfig: AppConfig,
                private auth: AuthService,
                private dialogService: MatDialog) { }

    ngOnInit() {
        this.reload();
    }

    public openCreateCollectionDialog() {
        let dialogRef = this.dialogService.open(AddCollectionComponent, {
            width: '520px'
        });
        dialogRef.afterClosed().subscribe((result) => {
            if (result) {
                this.reload();
            }
        });
    }

    private reload() {
        this.loading = true;
        this.error = undefined;
        const response = this.active ? this.collectionsService.getMyUnarchivedCollectionsPaginated() :
            this.collectionsService.getMyArchivedCollectionsPaginated();
        const temp = [];
        response.subscribe((collection: Collection) => {
            temp.push(<CollectionRow>{
                id: collection._id,
                title: collection.getTitleOrId(),
                creator: this.auth.getUserDisplayName(collection.creator_id),
                last_updated: collection._updated,
            });
        }, (error) => {
            this.error = `Error ${error.status}: ${error.message}`;
            this.loading = false;
        }, () => {
            temp.sort((a: CollectionRow, b: CollectionRow) => a.title.localeCompare(b.title));
            this.collections = temp;
            this.dataSource.data = this.collections;
            this.dataSource.paginator = this.paginator;
            this.loading = false;
        });
    }

    applyFilter(filterValue: string) {
        this.dataSource.filter = filterValue.trim().toLowerCase();
    }

    public archiveChanged(event) {
        this.active = event.value === "active";
        this.reload();
    }

}

