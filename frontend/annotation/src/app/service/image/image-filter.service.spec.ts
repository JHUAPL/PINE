import { TestBed } from '@angular/core/testing';

import { ImageFilterService } from './image-filter.service';

describe('ImageFilterService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ImageFilterService = TestBed.get(ImageFilterService);
    expect(service).toBeTruthy();
  });
});
