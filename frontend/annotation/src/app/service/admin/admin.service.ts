import { Injectable } from "@angular/core";
import { HttpResponse } from "@angular/common/http";

import { Observable } from "rxjs";
import { map } from "rxjs/operators";

import { BackendService } from "../backend/backend.service";

import { EveUser } from "../../model/user";
import { CreatedObject } from "../../model/created";

@Injectable({
    providedIn: "root"
})
export class AdminService {

    constructor(private backend: BackendService) {
    }

    public getAllUsers(): Observable<EveUser[]> {
        return this.backend.get<EveUser[]>("/admin/users");
    }

    public addUser(obj: any): Observable<CreatedObject> {
        return this.backend.post<CreatedObject>("/admin/users", obj);
    }

    public getUser(userId: string): Observable<EveUser> {
        return this.backend.get<EveUser>("/admin/users/" + userId);
    }

    public updateUser(userId: string, updatedUser: EveUser): Observable<CreatedObject> {
        return this.backend.put<CreatedObject>("/admin/users/" + userId, updatedUser);
    }

    public changeUserPassword(userId: string, new_password: string): Observable<CreatedObject> {
        return this.backend.put<CreatedObject>("/admin/users/" + userId + "/password",
                {"passwd": new_password});
    }

    public deleteUser(userId: string): Observable<any> {
        return this.backend.delete<any>("/admin/users/" + userId);
    }

    public systemExport(): Observable<HttpResponse<Blob>> {
        return this.backend.getBlob("/admin/system/export");
    }

    public systemImport(file: File, dumpFirst: boolean): Observable<boolean> {
        const form = new FormData();
        form.append("file", file, file.name);
        const resp = dumpFirst ?
                this.backend.postForm<any>("/admin/system/import", form) :
                    this.backend.putForm<any>("/admin/system/import", form);
        return resp.pipe(map(r => r.success));
    }

}
