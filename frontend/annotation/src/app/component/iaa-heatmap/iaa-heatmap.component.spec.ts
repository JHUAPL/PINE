/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { IaaHeatmapComponent } from './iaa-heatmap.component';

describe('IaaHeatmapComponent', () => {
  let component: IaaHeatmapComponent;
  let fixture: ComponentFixture<IaaHeatmapComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ IaaHeatmapComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(IaaHeatmapComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
