/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ViewChild, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort, MatSortable } from '@angular/material/sort';
import { MatTable, MatTableDataSource } from '@angular/material/table';

import { Observable } from "rxjs";

import { NerData } from "../annotate/ner-data";

import { DocLabel } from "../../model/doclabel";
import { NerAnnotation } from "../../model/annotation";

@Component({
  selector: 'app-ner-annotation-table',
  templateUrl: './ner-annotation-table.component.html',
  styleUrls: ['./ner-annotation-table.component.css']
})
export class NERAnnotationTableComponent implements OnInit {

    @Input()
    public labels: DocLabel[];

    @Input()
    public data: NerData;

    @Input()
    public readOnly: boolean;

    @Output()
    public remove = new EventEmitter<NerAnnotation>();

    @ViewChild(MatPaginator)
    public paginator: MatPaginator;

    @ViewChild(MatSort, { static: true })
    public sort: MatSort;

    @ViewChild(MatTable, { static: true })
    public table: MatTable<MatTableDataSource<NerAnnotation>>;

    public displayedColumns: string[] = ['text', 'label', 'start', 'end', 'actions'];

    public dataSource: MatTableDataSource<NerAnnotation>;

    constructor(
		private cdr: ChangeDetectorRef
	) {
        this.dataSource = new MatTableDataSource<NerAnnotation>();
        this.dataSource.filterPredicate = (annotation, value): boolean => {
            if(annotation.label.toLowerCase().includes(value)) {
                return true;
            }
            if(this.getAnnotationText(annotation).toLowerCase().includes(value)) {
                return true;
            }
            return false;
        };
    }

    ngOnInit() {
        this.data.changed.subscribe((res: NerAnnotation[]) => {
            this.dataSource.data = res;
			this.cdr.detectChanges();
        });
        this.dataSource.sortingDataAccessor = (annotation: NerAnnotation, property: string) => {
            switch(property) {
            case "text": return this.getAnnotationText(annotation);
            case "label": return annotation.label;
            case "start": return annotation.start;
            case "end": return annotation.end;
            default: return annotation[property];
            }
        };
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.sort.sort(<MatSortable>{
            id: "start",
            start: "asc"
          }
        );
    }

    public getLabelColor(name: string) {
        for(const label of this.labels) {
            if(label.name === name) {
                return label.color;
            }
        }
    }

    getAnnotationText(annotation: NerAnnotation) {
        let annotationStr = '';
        for(const word of this.data.words) {
            if(word.start >= annotation.start && word.end <= annotation.end) {
                annotationStr += word.text;
            } else if(word.start > annotation.end) {
                break;
            }
        }
        return annotationStr;
    }

    applyFilter(filterValue: string) {
        // Need fix to filter by annotation tokens
        this.dataSource.filter = filterValue.trim().toLowerCase();
    }

    removeAnnotation(annotation: NerAnnotation) {
        this.remove.emit(annotation);
    }

}
