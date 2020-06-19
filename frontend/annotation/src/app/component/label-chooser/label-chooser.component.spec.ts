/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LabelChooserComponent } from './label-chooser.component';

describe('LabelChooserComponent', () => {
  let component: LabelChooserComponent;
  let fixture: ComponentFixture<LabelChooserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LabelChooserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LabelChooserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
