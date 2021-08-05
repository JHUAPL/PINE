/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { UserChooserComponent } from './user-chooser.component';

describe('UserChooserComponent', () => {
  let component: UserChooserComponent;
  let fixture: ComponentFixture<UserChooserComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ UserChooserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserChooserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
