import { TestBed, inject } from '@angular/core/testing';

import { DocumentRepositoryService } from './document-repository.service';

describe('DocumentRepositoryService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [DocumentRepositoryService]
    });
  });

  it('should be created', inject([DocumentRepositoryService], (service: DocumentRepositoryService) => {
    expect(service).toBeTruthy();
  }));
});
