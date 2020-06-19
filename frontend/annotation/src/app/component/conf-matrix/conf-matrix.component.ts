/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-conf-matrix',
  templateUrl: './conf-matrix.component.html',
  styleUrls: ['./conf-matrix.component.css']
})
export class ConfMatrixComponent implements OnInit {

  constructor() { }

  @Input()
  data: any

  ngOnInit() {

  }



}
