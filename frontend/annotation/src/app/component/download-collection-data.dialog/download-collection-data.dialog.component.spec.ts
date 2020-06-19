/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DownloadCollectionDataComponent } from './download-collection-data.component';

describe('DownloadCollectionDataDialogComponent', () => {
  let component: DownloadCollectionDataDialogComponent;
  let fixture: ComponentFixture<DownloadCollectionDataDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DownloadCollectionDataDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DownloadCollectionDataDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
