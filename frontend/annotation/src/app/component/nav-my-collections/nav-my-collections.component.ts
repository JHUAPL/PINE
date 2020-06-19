/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ViewChildren, QueryList } from "@angular/core";

import { NavCollectionMenuComponent } from "../nav-collection-menu/nav-collection-menu.component";

import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";
import { EventService, AddedDocumentIds } from "../../service/event/event.service";

import { Collection } from "../../model/collection";
import { Document } from "../../model/document";

export interface CollectionData {
    id: string;
    title: string;
}

@Component({
  selector: "app-nav-my-collections",
  templateUrl: "./nav-my-collections.component.html",
  styleUrls: ["./nav-my-collections.component.css"]
})
export class NavMyCollectionsComponent implements OnInit {

    public collections: CollectionData[];

    @ViewChildren(NavCollectionMenuComponent)
    public menus: QueryList<NavCollectionMenuComponent>;

    constructor(private collectionsService: CollectionRepositoryService,
                private documentsService: DocumentRepositoryService,
                private event: EventService) { }

    ngOnInit() {
        this.refreshCollections();
        this.event.collectionAddedOrArchived.subscribe((collection: Collection) => {
            this.refreshCollections();
        });
        this.event.systemDataImported.subscribe(() => {
            this.refreshCollections();
        });
        this.event.documentAddedById.subscribe((ids: AddedDocumentIds) => {
            this.refreshCollection(ids.collectionId);
        });
    }

    private refreshCollections() {
        const temp = [];
        this.collectionsService.getMyUnarchivedCollectionsPaginated().subscribe((collection: Collection) => {
            temp.push(<CollectionData>{
                id: collection._id,
                title: collection.getTitleOrId()
            });
        }, (error) => {}, () => {
            temp.sort((a: CollectionData, b: CollectionData) => a.title.localeCompare(b.title));
            this.collections = temp;
        });
    }

    private refreshCollection(collectionId: string) {
        this.menus.find((_, index) => this.collections[index].id === collectionId).refresh();
    }
}
