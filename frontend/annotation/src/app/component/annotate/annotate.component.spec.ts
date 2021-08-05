/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { AnnotateComponent } from './annotate.component';

describe('AnnotateComponent', () => {
  let component: AnnotateComponent;
  let fixture: ComponentFixture<AnnotateComponent>;

  beforeEach(waitForAsync(() => {
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
