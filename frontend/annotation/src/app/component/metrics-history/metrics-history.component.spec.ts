/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MetricsHistoryComponent } from './metrics-history.component';

describe('MetricsHistoryComponent', () => {
  let component: MetricsHistoryComponent;
  let fixture: ComponentFixture<MetricsHistoryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MetricsHistoryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MetricsHistoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
