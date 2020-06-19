/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from "@angular/core/testing";

import { ImageCollectionUploaderComponent } from "./image-collection-uploader.component";

describe("ImageCollectionUploaderComponent", () => {
    let component: ImageCollectionUploaderComponent;
    let fixture: ComponentFixture<ImageCollectionUploaderComponent>;

    beforeEach(async(() => {
        TestBed.configureTestingModule({
            declarations: [ ImageCollectionUploaderComponent ]
        })
        .compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(ImageCollectionUploaderComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
