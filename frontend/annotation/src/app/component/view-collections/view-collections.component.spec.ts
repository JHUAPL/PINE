/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ViewCollectionsComponent } from './view-collections.component';

describe('ViewCollectionsComponent', () => {
  let component: ViewCollectionsComponent;
  let fixture: ComponentFixture<ViewCollectionsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ViewCollectionsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ViewCollectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
