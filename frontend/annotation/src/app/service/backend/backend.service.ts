import { Injectable } from "@angular/core";
import { HttpClient, HttpHeaders, HttpResponse } from "@angular/common/http";

import { Observable, defer, from, EMPTY, concat } from "rxjs";
import { mergeMap } from "rxjs/operators";

import { AppConfig } from "../../app.config";

import { DBObject, DBObjects } from "../../model/db";

@Injectable({
  providedIn: "root"
})
export class BackendService {

    private IEheaders = new HttpHeaders({
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Expires': 'Sat, 01 Jan 2000 00:00:00 GMT'
    });

    private formHeaders = new HttpHeaders({
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Expires': 'Sat, 01 Jan 2000 00:00:00 GMT',
        "Content-Type": "multipart/form-data"
    });

    constructor(private http: HttpClient) {
    }
    
    public frontendUrl(path: string): string {
        if(path.startsWith("/")) {
            const locationOrigin = `${window.location.origin ? window.location.origin : (window.location.protocol
                + '//' + window.location.hostname + (window.location.port ? (':' + window.location.port) : ''))}`;
            return locationOrigin + path;
        } else {
            return path;
        }
    }

    public collectionImageUrl(collectionId: string, url: string): string {
        if(url && url.startsWith("/")) {
            return `${AppConfig.settings.backend.host}/collections/image/${collectionId}${url}`;
        } else {
            return url;
        }
    }

    public get<T>(path: string, options = {}): Observable<T> {
        // console.log("GET " + path);
        return this.http.get<T>(AppConfig.settings.backend.host + path,
                { ...options, ...{withCredentials: true,  headers: this.IEheaders} });
    }

    public getBlob(path: string, options = {}): Observable<HttpResponse<Blob>> {
        return this.http.get(AppConfig.settings.backend.host + path,
                { ...options, ...{withCredentials: true,  headers: this.IEheaders,
                                  observe: "response", responseType: "blob"} });
    }

    public delete<T>(path: string, options = {}): Observable<T> {
        return this.http.delete<T>(AppConfig.settings.backend.host + path,
                {...options, ...{withCredentials: true, headers: this.IEheaders }});
    }

    public post<T>(path: string, data: object = {}, options = {}): Observable<T> {
        // console.log("POST " + path);
        return this.http.post<T>(AppConfig.settings.backend.host + path, data,
                {...options, ...{withCredentials: true, headers: this.IEheaders }});
    }

    public postForm<T>(path: string, form: FormData, options = {}): Observable<T> {
        // setting a header to "Content-Type": "multipart/form-data" makes this not work...
        return this.http.post<T>(AppConfig.settings.backend.host + path, form,
                {...options, ...{withCredentials: true, headers: this.IEheaders }});
    }

    public put<T>(path: string, data: object, options = {}): Observable<T> {
        return this.http.put<T>(AppConfig.settings.backend.host + path, data,
                {...options, ...{withCredentials: true, headers: this.IEheaders }});
    }

    public putForm<T>(path: string, form: FormData, options = {}): Observable<T> {
        return this.http.put<T>(AppConfig.settings.backend.host + path, form,
                {...options, ...{withCredentials: true, headers: this.IEheaders }});
    }

    public ping(): Observable<string> {
        return this.get<string>("/ping");
    }

    getItemsPaginated(fetchItems: (number) => Observable<DBObjects>, page: number = 1): Observable<DBObject> {
        return defer(() => fetchItems(page)).pipe(mergeMap((objects: DBObjects) => {
            const items$ = from(objects._items);
            let next$: Observable<DBObject | never> = EMPTY;
            if(objects._meta) {
                const totalPages = Math.ceil(objects._meta.total / objects._meta.max_results);
                if(page < totalPages) {
                    next$ = this.getItemsPaginated(fetchItems, page + 1);
                }
            }
            return concat(items$, next$);
        }));
    }
    
    public static downloadFile(response: HttpResponse<Blob>, defaultFilename: string, elem = null) {
        let filename = defaultFilename;
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(response.headers.get("Content-Disposition"));
        if(matches && matches[1]) {
            filename = matches[1].replace(/['"]/g, '');
        }
        const url = window.URL.createObjectURL(response.body);
        
        let link = elem == null ? document.createElement("a") : elem;
        
        link.href = url;
        link.download = filename;
        link.click();
        
        if(elem == null) {
            link.remove();
        }
        window.URL.revokeObjectURL(url);
    }

}
