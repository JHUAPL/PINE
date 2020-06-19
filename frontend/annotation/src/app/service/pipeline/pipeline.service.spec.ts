import { TestBed, inject } from '@angular/core/testing';

import { PipelineService } from './pipeline.service';

describe('PipelineService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [PipelineService]
    });
  });

  it('should be created', inject([PipelineService], (service: PipelineService) => {
    expect(service).toBeTruthy();
  }));
});
