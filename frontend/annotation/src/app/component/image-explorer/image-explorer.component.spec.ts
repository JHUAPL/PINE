import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImageExplorerComponent } from './image-explorer.component';

describe('ImageExplorerComponent', () => {
  let component: ImageExplorerComponent;
  let fixture: ComponentFixture<ImageExplorerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ImageExplorerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImageExplorerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
