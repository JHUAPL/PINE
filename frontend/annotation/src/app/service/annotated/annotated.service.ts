import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AnnotatedService {

  constructor() { }

  public documentAnnotated = new Subject<string>();


  changeDocumentStatus(document: any) {
    this.documentAnnotated.next(document);
  }



}
