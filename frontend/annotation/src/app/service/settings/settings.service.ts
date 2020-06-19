// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { Injectable } from '@angular/core';

import { CookieService } from "ngx-cookie-service";

@Injectable({
      providedIn: 'root'
})
export class SettingsService {

    public static readonly SETTINGS_COOKIE_NAME = "pine.settings";
    public static readonly SETTINGS_COOKIE_PATH = "/"
    public static readonly SETTINGS_COOKIE_SECURE = false;
    public static readonly SETTINGS_COOKIE_SAMESITE = "Strict";

    constructor(private cookies: CookieService) {
    }
    
    public getAll(): object {
        if(!this.cookies.check(SettingsService.SETTINGS_COOKIE_NAME)) {
            this.setAll({});
        }
        const s = this.cookies.get(SettingsService.SETTINGS_COOKIE_NAME);
        try {
            return JSON.parse(s);
        } catch(e) {
            if(e instanceof SyntaxError) {
                console.warn("\"" + s + "\" is not valid JSON for settings.");
                this.setAll({});
                return {};
            } else {
                throw e;
            }
        }
    }
    
    public setAll(value: object) {
        if(value == null || value == undefined) {
            value = {};
        }
        this.cookies.set(SettingsService.SETTINGS_COOKIE_NAME, JSON.stringify(value),
                         undefined,
                         SettingsService.SETTINGS_COOKIE_PATH,
                         undefined,
                         SettingsService.SETTINGS_COOKIE_SECURE,
                         SettingsService.SETTINGS_COOKIE_SAMESITE);
    }
    
    public get(key: string, defaultValue: any = null): any {
        const s = this.getAll();
        if(key in s) {
            return s[key];
        } else {
            return defaultValue;
        }
    }
    
    public set(key: string, value: any) {
        const s = this.getAll();
        s[key] = value;
        this.setAll(s);
    }

}
