// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { Injectable } from '@angular/core';

@Injectable({
      providedIn: 'root'
})
export class SettingsService {

    public static readonly SETTINGS_PREFIX = "pine.settings.";

    constructor() {
    }

    public getAll(prefix: string = SettingsService.SETTINGS_PREFIX): {[key: string]: any} {
        let values = {};
        for(const key in Object.keys(window.localStorage)) {
            if(prefix === undefined || prefix === null || key.startsWith(prefix)) {
                const value = window.localStorage.getItem(key);
                try {
                    values[key] = JSON.parse(value);
                } catch(e) {
                    if(e instanceof SyntaxError) {
                        console.warn("\"" + value + "\" is not valid JSON for settings.");
                    } else {
                        throw e;
                    }
                }
            }
        }
        return values;
    }

    public setAll(value: {[key: string]: any}) {
        if(value == null || value == undefined) {
            return;
        }
        for(const key in value) {
            this.set(key, value[key]);
        }
    }

    public has(key: string): boolean {
        const val = window.localStorage.getItem(key);
        return val !== undefined && val !== null;
    }

    public get<T>(key: string, defaultValue: T = null): T {
        let value = window.localStorage.getItem(key);
        if(value === null || value === undefined) {
            return defaultValue;
        } else {
            try {
                return JSON.parse(value);
            } catch(e) {
                if(e instanceof SyntaxError) {
                    console.warn("\"" + value + "\" is not valid JSON for settings.");
                    return defaultValue;
                } else {
                    throw e;
                }
            }
        }
    }

    public set(key: string, value: any) {
        if(value !== undefined && value !== null) {
            window.localStorage.setItem(key, JSON.stringify(value));
        } else {
            window.localStorage.removeItem(key);
        }
    }

}
