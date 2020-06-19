import { Injectable, EventEmitter } from '@angular/core';

import { Collection } from "../../model/collection";

export interface AddedDocumentIds {
    documentId: string;
    collectionId: string;
}

@Injectable({
  providedIn: 'root'
})
export class EventService {

    public showUserMessage: EventEmitter<string> = new EventEmitter();

    public collectionAddedOrArchived: EventEmitter<Collection> = new EventEmitter();

    public systemDataImported: EventEmitter<any> = new EventEmitter();

    //public documentAdded: EventEmitter<Document> = new EventEmitter();

    public documentAddedById: EventEmitter<AddedDocumentIds> = new EventEmitter();

    public logout: EventEmitter<any> = new EventEmitter();

    constructor() { }

}
