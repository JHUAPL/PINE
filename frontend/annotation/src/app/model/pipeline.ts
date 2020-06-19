// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject, DBObjects, ModelObject } from "./db";

export interface DBPipeline extends DBObject {
    title: string;
    description: string;
    parameters: object;
}

export interface DBPipelines extends DBObjects {
    _items: DBPipeline[];
}

export class Pipeline extends ModelObject implements DBPipeline {

    public title: string;
    public description: string;
    public parameters: object;

    public static fromDB(dbObj: DBPipeline): Pipeline {
        return <Pipeline>Object.setPrototypeOf(dbObj, new Pipeline());
    }

    public static fromDBItems(dbObjs: DBPipelines): Pipeline[] {
        return dbObjs._items.map(Pipeline.fromDB);
    }
}
