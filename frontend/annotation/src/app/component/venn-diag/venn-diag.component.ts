/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, AfterViewInit, AfterContentInit, ViewChild, ElementRef, Input, OnChanges, SimpleChanges } from '@angular/core';
import * as d3 from "d3";

import * as venn from 'venn.js';

@Component({
  selector: 'app-venn-diag',
  templateUrl: './venn-diag.component.html',
  styleUrls: ['./venn-diag.component.css']
})
export class VennDiagComponent implements OnInit, AfterViewInit, AfterContentInit, OnChanges {

  @ViewChild('venn', { static: true }) private vennContainer: ElementRef;

  @Input()
  data: any

  ngAfterContentInit(): void {
    
  }
  ngAfterViewInit(): void {
    
  }
  ngOnChanges(changes: SimpleChanges){
    let vennContainerElement = this.vennContainer.nativeElement
    var sets = [{ sets: ['False Negative'], size: this.data.FN },
    { sets: ['False Positive'], size: this.data.FP },
    { sets: ['False Negative', 'False Positive'], size: this.data.TP }];
    var chart = venn.VennDiagram();
    d3.select(vennContainerElement).datum(sets).call(chart);
  }

  constructor() { }

  ngOnInit() {

  }

}
