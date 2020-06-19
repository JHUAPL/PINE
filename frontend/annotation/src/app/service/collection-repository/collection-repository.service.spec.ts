import { TestBed, inject } from '@angular/core/testing';

import { CollectionRepositoryService } from './collection-repository.service';

describe('CollectionRepositoryService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [CollectionRepositoryService]
    });
  });

  it('should be created', inject([CollectionRepositoryService], (service: CollectionRepositoryService) => {
    expect(service).toBeTruthy();
  }));
});
