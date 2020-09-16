/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input, AfterContentInit, ViewChild, OnChanges } from '@angular/core';
import { Chart } from 'chart.js';


@Component({
  selector: 'app-metrics-history',
  templateUrl: './metrics-history.component.html',
  styleUrls: ['./metrics-history.component.css']
})
export class MetricsHistoryComponent implements OnInit, AfterContentInit, OnChanges {

  constructor() { }

  @ViewChild('historicChart') private historicChartRef;

  chart: any;

  @Input()
  label: string

  @Input()
  data: any

  sortedData : any[]

  ngOnInit() {
  }

  ngAfterContentInit() {
    

  }
  ngOnChanges() {
    if(!this.data.find((metric)=>metric.metrics.length < 1)){
      this.sortedData = this.data.reverse();
      this.updateChart();
    }
    
  }
  updateChart() {
    this.chart = new Chart(this.historicChartRef.nativeElement, {
      type: 'line',
      data: {
        labels: this.getDateLabels(),
        datasets: [{
          label: "Accuracy",
          data: this.getAccuracy(),  //Metrics
          borderColor: '#FF0000',
          fill: false
        },
        {
          label: "Precision",
          data: this.getPrecision(),  //Metrics
          borderColor: '#00AEFF',
          fill: false
        },
        {
          label: "Recall",
          data: this.getRecall(),  //Metrics
          borderColor: '#008000',
          fill: false
        }]
      },
      options: {
        legend: {
          display: true
        },
        scales: {
          xAxes: [{
            display: true
          }],
          yAxes: [{
            display: true
          }],
        }
      }
    });

  }

  getDateLabels(){
    return this.sortedData.map((metric)=> metric._updated)
  }

  getAccuracy(){
    return this.sortedData.map((metric)=> metric.metric_averages[this.label].acc * 100)
  }

  getPrecision(){
    return this.sortedData.map((metric)=> metric.metric_averages[this.label].precision * 100)
  }
  getRecall(){
    return this.sortedData.map((metric)=> metric.metric_averages[this.label].recall * 100) 
  }
}
