/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ConfMatrixComponent } from './conf-matrix.component';

describe('ConfMatrixComponent', () => {
  let component: ConfMatrixComponent;
  let fixture: ComponentFixture<ConfMatrixComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ConfMatrixComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfMatrixComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
