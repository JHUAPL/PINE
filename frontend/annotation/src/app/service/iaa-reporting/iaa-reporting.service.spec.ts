import { TestBed } from '@angular/core/testing';

import { IaaReportingService } from './iaa-reporting.service';

describe('IaaReportingService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: IaaReportingService = TestBed.get(IaaReportingService);
    expect(service).toBeTruthy();
  });
});
