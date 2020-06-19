/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, AfterViewInit, Input, Pipe, PipeTransform, OnChanges, AfterContentInit, Output, EventEmitter } from '@angular/core';
import { MetricsService } from 'src/app/service/metrics/metrics.service';
import { Metric } from 'src/app/model/metrics';

@Component({
  selector: 'app-metrics',
  templateUrl: './metrics.component.html',
  styleUrls: ['./metrics.component.css']
})
export class MetricsComponent implements OnInit, AfterContentInit, OnChanges {

  constructor() { }

  label: string = "Overall"

  epoch: number = 0

  confMatrixData: any = { FP: 0, FN: 0, TP: 0, TN: 0 }

  vennDiagramData: any = { FP: 0, FN: 0, TP: 0}

  historicData: any = { acc: 0, precision: 0, recall: 0}

  sortedMetrics: Metric[]

  dateDisabled : boolean = false

  @Input()
  metrics: any

  latest_avg_metrics: object

  ngOnInit() {

  }
  ngOnChanges() {
    this.latest_avg_metrics = this.metrics._items[this.metrics._items.length - 1].metric_averages
    //Remove initial empty metric
    console.log(this.metrics);
    const filteredMetrics = this.metrics._items.filter(a => {
      return a.metrics != null ? a.metrics.length > 0 : false
    })
    this.sortedMetrics = filteredMetrics.sort((a, b) => {
      if (a._updated < b._updated) {
        return -1
      } else if (b._updated < a._updated) {
        return 1
      } else {
        return 0
      }
    })
    this.updateVisualizationData()

  }
  ngAfterContentInit() {
    this.latest_avg_metrics = this.metrics._items[this.metrics._items.length - 1].metric_averages
    this.sortedMetrics = this.metrics._items.sort((a, b) => {
      if (a._updated < b._updated) {
        return -1
      } else if (b._updated < a._updated) {
        return 1
      } else {
        return 0
      }
    })
    this.updateVisualizationData()
  }

  selectLabel(label) {
    this.label = label == "Totals" ? "Overall" : label
    this.updateVisualizationData()
  }
  selectEpoch(epochIndex) {
    this.epoch = epochIndex
    this.updateVisualizationData()
  }

  updateVisualizationData() {
    this.updateConfusionMatrixData()
    this.updateVennDiagramData()
  }

  updateConfusionMatrixData() {
    if (this.sortedMetrics[this.epoch] && this.sortedMetrics[this.epoch].metric_averages) {
      const correctLabel = this.getCorrectLabel(this.label)
      this.confMatrixData.FP = this.sortedMetrics[this.epoch].metric_averages[correctLabel].FP
      this.confMatrixData.TP = this.sortedMetrics[this.epoch].metric_averages[correctLabel].TP
      this.confMatrixData.FN = this.sortedMetrics[this.epoch].metric_averages[correctLabel].FN
      this.confMatrixData.TN = this.sortedMetrics[this.epoch].metric_averages[correctLabel].TN
    }
  }
  updateVennDiagramData(){
    if (this.sortedMetrics[this.epoch] && this.sortedMetrics[this.epoch].metric_averages) {
      const correctLabel = this.getCorrectLabel(this.label)
      var newData = { FP: 0, FN: 0, TP: 0}
      newData.FP = this.sortedMetrics[this.epoch].metric_averages[correctLabel].FP
      newData.TP = this.sortedMetrics[this.epoch].metric_averages[correctLabel].TP
      newData.FN = this.sortedMetrics[this.epoch].metric_averages[correctLabel].FN
      this.vennDiagramData = newData
    }
  }


  getCorrectLabel(label) {
    return label == "Overall" ? "Totals" : label
  }

  changedTabs(event){
    if(event.tab.textLabel == "Historic Data"){
      this.dateDisabled = true;
    }else{
      this.dateDisabled = false;

    }
  }
}
