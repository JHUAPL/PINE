// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";

import { environment } from '../environments/environment';
import { IAppConfig } from './model/app.config';

import { PATHS } from "./app.paths";

@Injectable()
export class AppConfig {
    
    public static settings: IAppConfig;

    public appName = "PINE";

    public appLongName = "PMAP Interface for NLP Experimentation";

    public appLogoAsset = "tree_icon_sketch.png";

    public loginPage = `/${PATHS.user.login}`;

    public landingPage = `/${PATHS.collection.view}`;

    constructor(private http: HttpClient) { }

    load() {
        const jsonFile = `assets/config/config.${environment.name}.json`;
        return new Promise<void>((resolve, reject) => {
            this.http.get<IAppConfig>(jsonFile).subscribe((settings: IAppConfig) => {
               AppConfig.settings = settings;
               resolve();
            }, (error: any) => {
               reject(`Could not load file '${jsonFile}': ${JSON.stringify(error)}`);
            });
        });
    }
}
