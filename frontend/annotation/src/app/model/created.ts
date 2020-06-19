// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { DBObject } from "./db";

export interface CreatedObject extends DBObject {
    _status: string;
}
