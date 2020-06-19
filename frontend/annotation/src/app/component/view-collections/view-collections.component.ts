/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ViewChild } from "@angular/core";
import { MatPaginator, MatTableDataSource } from "@angular/material";

import { PATHS } from "../../app.paths";
import { AppConfig } from "../../app.config";

import { LoadingComponent } from "../loading/loading.component";

import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { AuthService } from "../../service/auth/auth.service";

import { Collection } from "../../model/collection";

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

    @ViewChild(LoadingComponent)
    public loading: LoadingComponent;

    public active = true;

    collections: CollectionRow[];
    selected = null;

    displayedColumns: string[] = ["title", "creator", "last_updated"];
    dataSource = new MatTableDataSource<CollectionRow>(this.collections);

    @ViewChild(MatPaginator)
    paginator: MatPaginator;

    constructor(public collectionsService: CollectionRepositoryService,
                public appConfig: AppConfig,
                private auth: AuthService) { }

    ngOnInit() {
        this.reload();
    }

    private reload() {
        this.loading.loading = true;
        this.loading.clearError();
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
            this.loading.setError(`Error ${error.status}: ${error.message}`);
            this.loading.loading = false;
        }, () => {
            temp.sort((a: CollectionRow, b: CollectionRow) => a.title.localeCompare(b.title));
            this.collections = temp;
            this.dataSource.data = this.collections;
            this.dataSource.paginator = this.paginator;
            this.loading.loading = false;
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

