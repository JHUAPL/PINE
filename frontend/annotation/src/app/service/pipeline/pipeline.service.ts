import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

import { AuthService } from "../auth/auth.service";
import { BackendService } from "../backend/backend.service";

import { DBClassifier, Classifier } from "../../model/classifier";
import { DBPipeline, DBPipelines, Pipeline } from "../../model/pipeline";

@Injectable({
    providedIn: "root"
})
export class PipelineService {

    constructor(private backend: BackendService, private auth: AuthService) { }

    public getAllPipelines(): Observable<Pipeline[]> {
        return this.backend.get<DBPipelines>("/pipelines").pipe(map(Pipeline.fromDBItems));
    }

    public getPipeline(pipeline_id: string): Observable<Pipeline> {
        return this.backend.get<DBPipeline>(`/pipelines/by_id/${pipeline_id}`).pipe(map(Pipeline.fromDB));
    }

    public getClassifierForCollection(collectionId: string): Observable<Classifier> {
        return this.backend.get<DBClassifier>(`/pipelines/classifiers/by_collection_id/${collectionId}`).pipe(map(Classifier.fromDB));
    }

    public getNextDocumentIdForClassifier(classifierId: string): Observable<string | null> {
        return this.backend.get<string | null>(`/pipelines/next_document/by_classifier_id/${classifierId}`);
    }

    public advanceToNextDocumentForClassifier(classifierId: string, documentId: string): Observable<boolean> {
        const url = `/pipelines/next_document/by_classifier_id/${classifierId}/${documentId}`;
        return this.backend.post<object>(url).pipe(map((ret: object) => ret["success"]));
    }

}
