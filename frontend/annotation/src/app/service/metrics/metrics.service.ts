import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

import { AuthService } from "../auth/auth.service";
import { BackendService } from "../backend/backend.service";

import { DBClassifier, Classifier } from "../../model/classifier";
import { DBMetric, DBMetrics, Metric } from "../../model/metrics";

@Injectable({
    providedIn: "root"
})
export class MetricsService {

    constructor(private backend: BackendService, private auth: AuthService) { }

    public getAllMetrics(): Observable<Metric[]> {
        return this.backend.get<DBMetrics>("/pipelines/metrics").pipe(map(Metric.fromDBItems));
    }

    public getMetric(metric_id: string): Observable<Metric> {
        return this.backend.get<DBMetric>(`/pipelines/metrics/by_id/${metric_id}`).pipe(map(Metric.fromDB));
    }

    public getMetricForClassifier(classifierId: string): Observable<Metric> {
        return this.backend.get<DBMetric>(`/pipelines/metrics/by_classifier_id/${classifierId}`).pipe(map(Metric.fromDB));
    }

}
