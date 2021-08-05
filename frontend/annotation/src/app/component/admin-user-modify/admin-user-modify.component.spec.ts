/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { AdminUserModifyComponent } from './admin-user-modify.component';

describe('AdminUserModifyComponent', () => {
  let component: AdminUserModifyComponent;
  let fixture: ComponentFixture<AdminUserModifyComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AdminUserModifyComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AdminUserModifyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
