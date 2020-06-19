/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NavMyCollectionsComponent } from './nav-my-collections.component';

describe('NavMyCollectionsComponent', () => {
  let component: NavMyCollectionsComponent;
  let fixture: ComponentFixture<NavMyCollectionsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ NavMyCollectionsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NavMyCollectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
