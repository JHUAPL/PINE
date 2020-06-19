/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { VennDiagComponent } from './venn-diag.component';

describe('VennDiagComponent', () => {
  let component: VennDiagComponent;
  let fixture: ComponentFixture<VennDiagComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ VennDiagComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(VennDiagComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
