import { Injectable } from '@angular/core';
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

import { BackendService } from "../backend/backend.service";

import { DBAnnotation, DBAnnotations, Annotation, NerAnnotation } from "../../model/annotation";

@Injectable({
    providedIn: 'root'
})
export class AnnotationService {

    constructor(private backend: BackendService) {
    }

    public getMyAnnotationsForDocument(docId: string): Observable<Annotation[]> {
        return this.backend.get<DBAnnotations>("/annotations/mine/by_document_id/" + docId).pipe(map(Annotation.fromDBItems));
    }

    public getOthersAnnotationsForDocument(docId: string): Observable<Annotation[]> {
        return this.backend.get<DBAnnotations>("/annotations/others/by_document_id/" + docId).pipe(map(Annotation.fromDBItems));
    }

    public saveAnnotations(docId: string, labels: string[], annotations: NerAnnotation[], updateIaa: boolean = true): Observable<string> {
        const body = {
          "doc": labels,
          "ner": annotations,
        };
        return this.backend.post<string>("/annotations/mine/by_document_id/" + docId, body, {
          "params": {
            "update_iaa": updateIaa
          }
        });
    }

}
