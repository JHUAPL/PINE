// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

export interface DBObject {
    _id: string;
    _updated: Date;
    _created: Date;
    _etag: string;
    _links?: object;
    _latest_version?: number;
    _version?: number;
}

export class ModelObject implements DBObject {

    public _id: string;
    public _updated: Date;
    public _created: Date;
    public _etag: string;
    public _links?: object;
    public _latest_version?: number;
    public _version?: number;

}

export interface DBMeta {
    page: number;
    total: number;
    max_results: number;
}

export interface DBObjects {
    _items: DBObject[];
    _links?: object;
    _meta?: DBMeta;
}
