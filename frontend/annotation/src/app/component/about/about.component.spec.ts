/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { ComponentFixture, TestBed, waitForAsync } from "@angular/core/testing";

import { AboutComponent } from "./about.component";

describe("AboutComponent", () => {
    let component: AboutComponent;
    let fixture: ComponentFixture<AboutComponent>;

    beforeEach(waitForAsync(() => {
        TestBed.configureTestingModule({
            declarations: [ AboutComponent ]
        })
        .compileComponents();
    }));

    beforeEach(() => {
        fixture = TestBed.createComponent(AboutComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it("should create", () => {
        expect(component).toBeTruthy();
    });
});
