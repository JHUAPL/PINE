// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject, DBObjects, ModelObject } from "./db";

export interface DBMetric extends DBObject {
    collection_id: string;
    classifier_id: string;
    classifier_version: number;
    documents: string[];
    annotations: string[];
    folds: string[];
    metrics: object[];
}

export interface DBMetrics extends DBObjects {
    _items: DBMetric[];
}

export class Metric extends ModelObject implements DBMetric {

    public collection_id: string;
    public classifier_id: string;
    public classifier_version: number;
    public documents: string[];
    public annotations: string[];
    public folds: string[];
    public metrics: object[];
    public metric_averages: object;

    public static fromDB(dbObj: DBMetric): Metric {
        return <Metric>Object.setPrototypeOf(dbObj, new Metric());
    }

    public static fromDBItems(dbObjs: DBMetrics): Metric[] {
        return dbObjs._items.map(Metric.fromDB);
    }
}
