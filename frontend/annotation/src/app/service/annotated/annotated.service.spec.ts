import { TestBed } from '@angular/core/testing';

import { AnnotatedService } from './annotated.service';

describe('AnnotatedService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: AnnotatedService = TestBed.get(AnnotatedService);
    expect(service).toBeTruthy();
  });
});
