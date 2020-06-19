/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, Input } from '@angular/core';
import { IAAReport } from 'src/app/model/iaareport';

@Component({
  selector: 'app-collection-iaa-report',
  templateUrl: './collection-iaa-report.component.html',
  styleUrls: ['./collection-iaa-report.component.css']
})
export class CollectionIaaReportComponent implements OnInit {

  constructor() { }

  @Input()
  iaa_report : IAAReport

  ngOnInit() {
    console.log(this.iaa_report)
  }

}
