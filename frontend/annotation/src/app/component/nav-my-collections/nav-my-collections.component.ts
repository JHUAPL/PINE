/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ViewChildren, QueryList } from "@angular/core";

import { Observable } from "rxjs";
import { map, toArray, tap, take } from "rxjs/operators";

import { NavCollectionMenuComponent } from "../nav-collection-menu/nav-collection-menu.component";

import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { EventService, AddedDocumentIds } from "../../service/event/event.service";

import { Collection } from "../../model/collection";

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

    public loading = true;

    public collections: CollectionData[];

    @ViewChildren(NavCollectionMenuComponent)
    public menus: QueryList<NavCollectionMenuComponent>;

    constructor(private collectionsService: CollectionRepositoryService,
                private event: EventService) { }

    ngOnInit() {
        this.refreshCollectionsAsync();
        this.event.collectionAddedOrArchived.subscribe((_: Collection) => {
            this.refreshCollectionsAsync();
        });
        this.event.systemDataImported.subscribe(() => {
            this.refreshCollectionsAsync();
        });
        this.event.documentAddedById.subscribe((ids: AddedDocumentIds) => {
            this.refreshCollectionAsync(ids.collectionId);
        });
    }
    
    private refreshCollectionsAsync() {
        this.loading = true;
        this.refreshCollections$().pipe(take(1)).subscribe(() => this.loading = false);
    }

    private refreshCollections$(): Observable<CollectionData[]> {
        return this.collectionsService.getMyUnarchivedCollectionsPaginated().pipe(
            map((collection: Collection) => <CollectionData>{
                id: collection._id,
                title: collection.getTitleOrId()
            }),
            toArray(),
            tap((collections: CollectionData[]) => this.collections = collections)
        );
    }
    
    private refreshCollectionAsync(collectionId: string) {
        this.refreshCollection$(collectionId).pipe(take(1)).subscribe();
    }

    private refreshCollection$(collectionId: string): Observable<void> {
        return this.menus.find((_, index) => this.collections[index].id === collectionId)
            .reload().pipe(map(() => undefined));
    }
}
