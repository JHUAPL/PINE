import { Injectable } from '@angular/core';
import { BackendService } from '../backend/backend.service';
import { DBIAAReports, IAAReport } from 'src/app/model/iaareport';
import { map } from 'rxjs/operators';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class IaaReportingService {

  constructor(private backend : BackendService) { }

  createIAAReport(collection_id){
    return this.backend.post<any>('/iaa_reports/by_collection_id/' + collection_id)
  }
  getIIAReportByCollection(collection_id): Observable<IAAReport[]>{
    return this.backend.get<DBIAAReports>('/iaa_reports/by_collection_id/' + collection_id).pipe(map(IAAReport.fromDBItems))
  }
}
