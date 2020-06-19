/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CollectionIaaReportComponent } from './collection-iaa-report.component';

describe('CollectionIaaReportComponent', () => {
  let component: CollectionIaaReportComponent;
  let fixture: ComponentFixture<CollectionIaaReportComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CollectionIaaReportComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CollectionIaaReportComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
