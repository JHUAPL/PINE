/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Input, ViewChild, ElementRef, AfterViewInit, OnChanges, SimpleChanges } from '@angular/core';
@Component({
  selector: 'app-iaa-heatmap',
  templateUrl: './iaa-heatmap.component.html',
  styleUrls: ['./iaa-heatmap.component.css']
})
export class IaaHeatmapComponent implements OnInit, AfterViewInit, OnChanges {

  HEATMAP_RECT_INITIAL_X = 175
  HEATMAP_RECT_INITIAL_Y = 50

  HEATMAP_SQUARE_SIZE = 50

  COLORBAR_RECT_INITIAL_X = 50
  COLORBAR_RECT_INITIAL_Y = 50

  constructor() { }

  @Input()
  heatmap_data: any

  flattened_data = []

  @ViewChild('canvas')
  canvas: ElementRef<HTMLCanvasElement>;

  private ctx: CanvasRenderingContext2D

  ngOnInit() {
    this.flattenData(this.heatmap_data)
    this.ctx = this.canvas.nativeElement.getContext('2d')
  }
  ngOnChanges(changes: SimpleChanges){
    if(changes.heatmap_data){
      if(!changes.heatmap_data.firstChange){
        this.updateHeatmap()
      }
    }
  }
  ngAfterViewInit(): void {
    this.updateHeatmap()
  }
  updateHeatmap(){
    this.setCanvasDimensions()
    this.drawColorBar()
    this.drawHeatMap()
  }
  setCanvasDimensions() {
    this.setCanvasWidth()
    this.setCanvasHeight()
  }
  setCanvasWidth() {
    var num_of_annotators = this.heatmap_data.annotators.length
    var annotators_width = 50 * num_of_annotators
    var width = this.HEATMAP_RECT_INITIAL_X + annotators_width + 125
    this.canvas.nativeElement.width = width
  }
  setCanvasHeight() {
    var num_of_annotators = this.heatmap_data.annotators.length
    var annotators_height = (50 * num_of_annotators) + 75
    var min_height = this.COLORBAR_RECT_INITIAL_Y + 255 + 50
    var height = annotators_height < min_height ? min_height : annotators_height + 125
    this.canvas.nativeElement.height = height
  }
  drawHeatMap() {
    //Draw Heatmap fill
    this.heatmap_data.matrix.forEach((element, index) => {
      element.forEach((element2, index2) => {
        var color_value = element2 * 255
        this.ctx.fillStyle = 'rgb(0, ' + color_value + ', ' + color_value + ')';
        var rectX = (index2 * this.HEATMAP_SQUARE_SIZE) + this.HEATMAP_RECT_INITIAL_X
        var rectY = (index * this.HEATMAP_SQUARE_SIZE) + this.HEATMAP_RECT_INITIAL_Y
        var rectWH = this.HEATMAP_SQUARE_SIZE
        this.ctx.fillRect(rectX, rectY, rectWH, rectWH)

        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";
        this.ctx.fillStyle = "white"
        this.ctx.fillText(((element2 * 100).toFixed().toString() + "%").toString(), rectX + (rectWH / 2), rectY + (rectWH / 2))
      });


    });
    //Draw Heatmap border
    this.ctx.fillStyle = "black"
    this.ctx.strokeRect(this.HEATMAP_RECT_INITIAL_X, 1 + this.HEATMAP_RECT_INITIAL_Y, (this.heatmap_data.annotators.length * this.HEATMAP_SQUARE_SIZE) - 1, (this.heatmap_data.annotators.length * this.HEATMAP_SQUARE_SIZE) - 1)

    //Draw Heapmap labels
    const num_of_annotators = this.heatmap_data.annotators.length
    const x_labels_y = this.HEATMAP_SQUARE_SIZE * num_of_annotators + this.HEATMAP_RECT_INITIAL_Y + 10
    const y_labels_x = this.HEATMAP_SQUARE_SIZE * num_of_annotators + this.HEATMAP_RECT_INITIAL_X + 10
    this.heatmap_data.annotators.forEach((annotator, index) => {
      var y_labels_y = this.HEATMAP_RECT_INITIAL_Y + (this.HEATMAP_SQUARE_SIZE * index) + this.HEATMAP_SQUARE_SIZE / 2
      var x_labels_x = this.HEATMAP_RECT_INITIAL_X + (this.HEATMAP_SQUARE_SIZE * index) + this.HEATMAP_SQUARE_SIZE / 2
      this.ctx.textAlign = "start";
      this.ctx.textBaseline = "middle";
      this.ctx.fillStyle = "black"
      this.ctx.fillText(annotator, y_labels_x, y_labels_y)
      this.ctx.save()
      this.ctx.rotate(0.5 * Math.PI)
      this.ctx.fillText(annotator, x_labels_y, -x_labels_x)
      this.ctx.restore()

    })
  }
  drawColorBar() {

    //Fill
    for (var i = 0; i <= 255; i++) {
      this.ctx.beginPath();
      var color = 'rgb(0, ' + (255 - i) + ', ' + (255 - i) + ')';
      this.ctx.fillStyle = color;
      this.ctx.fillRect(50, i + 50, 30, 1);
    }
    //draw measure %s
    for (let index = 0; index < 10; index++) {
      const lineX = 30 + this.COLORBAR_RECT_INITIAL_X
      const lineY = ((255 / 10) * index) + this.COLORBAR_RECT_INITIAL_Y + 1
      this.drawColorBarLine(lineX, lineY)
      this.drawColorBarText((100 - (index * 10) + "%").toString(), lineX + 10, lineY)
    }
    //Draw last line 0%
    const lineX = 30 + this.COLORBAR_RECT_INITIAL_X
    const lineY = 255 + this.COLORBAR_RECT_INITIAL_Y
    this.drawColorBarLine(lineX, lineY)
    this.drawColorBarText((0 + "%").toString(), lineX + 10, lineY)

    //Draw border
    this.ctx.fillStyle = "black"
    this.ctx.strokeRect(51, 1 + 50, 29, 254)
  }

  drawColorBarLine(x, y) {
    this.ctx.beginPath();
    this.ctx.moveTo(x, y);
    this.ctx.lineTo(x + 5, y);
    this.ctx.stroke();

  }

  drawColorBarText(text, x, y) {
    this.ctx.textAlign = "start";
    this.ctx.textBaseline = "middle";
    this.ctx.fillStyle = "black"
    this.ctx.fillText(text, x, y)

  }
  flattenData(heatmap_data: any) {
    heatmap_data.annotators.forEach((annotator, index) => {
      this.flattened_data.push(annotator)
      this.flattened_data = this.flattened_data.concat(heatmap_data.matrix[index].map((element) => (element * 100).toFixed(2).toString() + "%"))
    });
    this.flattened_data.push("")
    this.flattened_data = this.flattened_data.concat(heatmap_data.annotators)
  }

}
