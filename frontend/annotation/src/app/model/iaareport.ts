// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject, DBObjects, ModelObject } from "./db";

export interface DBIAAReport extends DBObject {
    collection_id: string;
    num_of_annotators: number;
    num_of_agreement_docs: number;
    num_of_labels: number;
    per_doc_agreement: object[];
    per_label_agreement: object[];
    overall_agreement: object[];
    labels_per_annotator : object
}

export interface DBIAAReports extends DBObjects {
    _items: IAAReport[];
}

export class IAAReport extends ModelObject implements DBIAAReport {

    collection_id: string;
    num_of_annotators: number;
    num_of_agreement_docs: number;
    num_of_labels: number;
    per_doc_agreement: object[];
    per_label_agreement: object[];
    overall_agreement: any;
    labels_per_annotator : object

    public static fromDB(dbObj: DBIAAReport): IAAReport {
        return <DBIAAReport>Object.setPrototypeOf(dbObj, new IAAReport());
    }

    public static fromDBItems(dbObjs: DBIAAReports): IAAReport[] {
        return dbObjs._items.map(IAAReport.fromDB);
    }
}
