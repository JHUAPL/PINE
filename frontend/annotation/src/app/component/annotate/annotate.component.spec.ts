/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AnnotateComponent } from './annotate.component';

describe('AnnotateComponent', () => {
  let component: AnnotateComponent;
  let fixture: ComponentFixture<AnnotateComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AnnotateComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AnnotateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
