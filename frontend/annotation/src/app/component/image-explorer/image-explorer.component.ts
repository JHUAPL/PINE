import { Component, OnInit, Input, OnChanges, SimpleChanges, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { PanZoomConfig, PanZoomAPI, PanZoomModel } from 'ngx-panzoom';
import { Subscription } from 'rxjs';

import { BackendService } from "../../service/backend/backend.service";
import { ImageFilterService } from 'src/app/service/image/image-filter.service';

@Component({
    selector: 'app-image-explorer',
    templateUrl: './image-explorer.component.html',
    styleUrls: ['./image-explorer.component.css']
})
export class ImageExplorerComponent implements OnInit, OnChanges, OnDestroy {

    @Input() documentId: string;
    @Input() collectionId: string;
    @Input() imageUrl: string;
    @ViewChild('imageCanvas', { static: true }) imageCanvas: ElementRef<HTMLCanvasElement>;

    private canvasContext;
    private img;
    public loadError;

    public mode: 'none' | 'invert' | 'histogram' | 'sharpen' = 'none';

    private panZoomAPI: PanZoomAPI;
    private apiSubscription: Subscription;
    public panZoomConfig: PanZoomConfig = new PanZoomConfig({
    });

    constructor(private backend: BackendService, private imageFilter: ImageFilterService) { }

    ngOnInit() {
        this.apiSubscription = this.panZoomConfig.api.subscribe((api: PanZoomAPI) => this.panZoomAPI = api);
    }

    ngOnDestroy(): void {
        this.apiSubscription.unsubscribe();
    }

    ngAfterViewInit() {
        this.canvasContext = this.imageCanvas.nativeElement.getContext('2d');
        this.updateImage(true);
    }

    ngOnChanges(change: SimpleChanges) {
        this.loadError = false;
        this.img = undefined;
        this.clearCanvas();

        let img = new Image;
        img.onload = () => {
            this.img = img;
            this.updateImage(true);
        };
        img.onerror = () => {
            this.clearCanvas();
            this.loadError = true;
        };

        if (!this.imageUrl.startsWith("/")) {
            img.crossOrigin = 'anonymous';
        } else {
            img.crossOrigin = 'use-credentials';
        }
        img.src = this.backend.collectionImageUrl(this.collectionId, this.imageUrl);
    }

    public setMode(mode: 'none' | 'invert' | 'histogram' | 'sharpen') {
        if (!this.img) {
            this.mode = 'none';
            return;
        }

        if (mode === 'none') {
            this.mode = 'none';
        } else {
            if (this.mode === mode) {
                this.mode = 'none';
            } else {
                this.mode = mode;
            }
        }
        this.updateImage();
    }

    public zoomIn() {
        if (!this.img) {
            return;
        }

        this.panZoomAPI.zoomIn();
    }

    public zoomOut() {
        if (!this.img) {
            return;
        }

        this.panZoomAPI.zoomOut();
    }

    public centerImage() {
        if (!this.img) {
            return;
        }

        this.panZoomAPI.zoomToFit({
            x: 0,
            y: 0,
            width: this.img.width,
            height: this.img.height
        }, 0);
    }

    private clearCanvas() {
        if (!this.canvasContext) {
            return;
        }
        this.canvasContext.clearRect(0, 0, this.canvasContext.canvas.width, this.canvasContext.canvas.height);
    }

    private updateImage(center: boolean = false) {
        if (!this.img) {
            return;
        }

        if (center) {
            this.panZoomAPI.zoomToFit({
                x: 0,
                y: 0,
                width: this.img.width,
                height: this.img.height
            }, 0);
        }

        if (this.mode === 'histogram') {
            this.canvasContext.canvas.width = this.img.width;
            this.canvasContext.canvas.height = this.img.height;
            let data = this.imageFilter.histogramEqualize(this.img);
            this.canvasContext.putImageData(data, 0, 0);
        } else if (this.mode === 'sharpen') {
            this.canvasContext.canvas.width = this.img.width;
            this.canvasContext.canvas.height = this.img.height;
            let data = this.imageFilter.sharpen(this.img);
            this.canvasContext.putImageData(data, 0, 0);
        } else {
            this.canvasContext.canvas.width = this.img.width;
            this.canvasContext.canvas.height = this.img.height;
            this.canvasContext.drawImage(this.img, 0, 0, this.img.width, this.img.height);
        }
    }

}
