/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, AfterViewInit, ViewChild, ViewChildren, ElementRef, QueryList } from "@angular/core";
import { ActivatedRoute, ParamMap, Router } from "@angular/router";
import { HttpErrorResponse } from "@angular/common/http";
import { MatDialog } from "@angular/material";
import { PanZoomConfig, PanZoomAPI, PanZoomModel } from 'ng2-panzoom';

import { forkJoin } from "rxjs";

import tippy from "tippy.js/dist/tippy.all";

import { ErrorComponent } from "../error/error.component";
import { LoadingComponent } from "../loading/loading.component";

import { confirm } from "../message.dialog/message.dialog.component";

import { AnnotationService } from "../../service/annotation/annotation.service";
import { CollectionRepositoryService } from "../../service/collection-repository/collection-repository.service";
import { DocumentRepositoryService } from "../../service/document-repository/document-repository.service";
import { EventService } from "../../service/event/event.service";
import { PipelineService } from "../../service/pipeline/pipeline.service";
import { AuthService } from "../../service/auth/auth.service";
import { SettingsService } from "../../service/settings/settings.service";

import { LeftMouseDown } from "../../service/utils";

import { Annotation, NerAnnotation } from "../../model/annotation";
import { Classifier } from "../../model/classifier";
import { Collection } from "../../model/collection";
import { Document } from "../../model/document";
import { DocLabel } from "../../model/doclabel";
import { Word } from "../../model/word";

import { NerData } from "./ner-data";
import { NerSelection } from "./ner-selection";

import { PATHS, PARAMS } from "../../app.paths";
import { AnnotatedService } from 'src/app/service/annotated/annotated.service';
import { IaaReportingService } from 'src/app/service/iaa-reporting/iaa-reporting.service';
import { IAAReport } from 'src/app/model/iaareport';

class DocAnnotation {
    constructor(public label: DocLabel, public checked: boolean) {
    }
}

@Component({
    selector: "app-annotate",
    templateUrl: "./annotate.component.html",
    styleUrls: ["./annotate.component.css"]
})
export class AnnotateComponent implements OnInit, AfterViewInit {

    public static readonly SUBTITLE = "Annotate Document";
    public static readonly SETTINGS_KEY = "annotation";

    public readonly PATHS = PATHS;

    @ViewChild('imageContainer') imageRef;

    @ViewChild(LoadingComponent)
    public loading: LoadingComponent;

    @ViewChild(ErrorComponent)
    public error: ErrorComponent;

    @ViewChild("docElem")
    public docElem: ElementRef;
    private selectionChangeTimer;
    private mouseDown: LeftMouseDown;

    public canAnnotate = false;
    public canCurrentlyAnnotate = false; // for showing others' annotations
    public allowOverlappingNerAnnotations = true;
    public showingAnnotationsFor: string = null;

    public doc: Document;
    public collection: Collection;
    private classifier: Classifier;
    public nerData: NerData;
    private currentSelection: NerSelection;

    public availableLabels: DocLabel[];
    public myDocAnnotations: DocAnnotation[];
    public myNerAnnotations: NerAnnotation[];
    public others: string[];
    public othersDocAnnotations: { [s: string]: string[]; };
    public othersNerAnnotations: { [s: string]: NerAnnotation[]; };

    private mouseOutState = false;
    private recentWord = null;

    public ann_agreement: number
    @ViewChildren("wordsList")
    public wordsList: QueryList<any>;

    @ViewChild("popoverTemplate")
    public popoverTemplate: ElementRef;
    public changed = false;

    constructor(private route: ActivatedRoute,
        private router: Router,
        private annotations: AnnotationService,
        private documents: DocumentRepositoryService,
        private collections: CollectionRepositoryService,
        private pipelines: PipelineService,
        private events: EventService,
        public auth: AuthService,
        private dialog: MatDialog,
        private annotatedService: AnnotatedService,
        private iaa_reporting: IaaReportingService,
        private settings: SettingsService) {
        this.mouseDown = new LeftMouseDown();
        this.nerData = new NerData();
        this.currentSelection = new NerSelection();
    }

    ngOnInit() {
    }

    ngAfterViewInit() {
        this.wordsList.changes.subscribe(t => {
            if (this.wordsList.last) {
                Promise.resolve().then(() => {
                    this.wordsLoaded();
                });
            }
        });
        this.loading.loading = true;
        this.loading.clearError();

        this.currentSelection.clear(true);
        this.removeAllAnnotations();
        this.changed = false;

        this.route.paramMap.subscribe((params: ParamMap) => {
            const docId = params.get(PARAMS.document.annotate.document_id);

            this.documents.getDocumentDetails(docId).subscribe((doc: Document) => {
                this.doc = doc;
                forkJoin(this.documents.getUserCanAnnotate(docId),
                    this.collections.getCollectionDetails(this.doc.collection_id),
                    this.annotations.getMyAnnotationsForDocument(docId),
                    this.annotations.getOthersAnnotationsForDocument(docId),
                    this.pipelines.getClassifierForCollection(this.doc.collection_id))
                    .subscribe((results: any[]) => {
                        this.canAnnotate = results[0];
                        this.collection = results[1];
                        const myAnnotations: Annotation[] = results[2];
                        const othersAnnotations: Annotation[] = results[3];
                        this.classifier = results[4];

                        this.canCurrentlyAnnotate = this.canAnnotate;
                        this.showingAnnotationsFor = null;
                        this.allowOverlappingNerAnnotations = this.collection.getAllowOverlappingNerAnnotations(true);
                        this.currentSelection.setAllowOverlappingAnnotations(this.allowOverlappingNerAnnotations);

                        this.availableLabels = DocLabel.getLabels(this.collection.labels);
                        this.myDocAnnotations = [];
                        const myDocLabels: string[] = Annotation.getDocLabels(myAnnotations);
                        for (const label of this.availableLabels) {
                            this.myDocAnnotations.push(new DocAnnotation(label,
                                myDocLabels.includes(label.name)));
                        }

                        this.myNerAnnotations = Annotation.getNerAnnotations(myAnnotations);
                        this.nerData.setWordsAndAnnotations(
                            Word.parseWordObjects(this.doc.text),
                            this.myNerAnnotations);
                        this.othersDocAnnotations = Annotation.getDocLabelsMap(othersAnnotations);
                        this.othersNerAnnotations = Annotation.getNerAnnotationsMap(othersAnnotations);
                        this.others = Object.keys(this.othersDocAnnotations).concat(Object.keys(this.othersNerAnnotations));
                        this.others = this.others.filter((value, index) => this.others.indexOf(value) === index);
                        this.others.sort((v1, v2) => this.auth.getUserDisplayName(v1).localeCompare(this.auth.getUserDisplayName(v2)));

                        this.loading.loading = false;
                        this.iaa_reporting.getIIAReportByCollection(this.doc.collection_id).toPromise().then((report: IAAReport[]) => {
                            if (report[0]) {
                                this.ann_agreement = report[0].per_doc_agreement[report[0].per_doc_agreement.findIndex((doc) => doc["doc_id"] == this.doc._id)]["avg"]
                            }
                        })
                    }, (error: HttpErrorResponse) => {
                        this.loading.setError(`Error ${error.status}: ${error.error}`);
                        this.loading.loading = false;
                    }
                    );
            }, (error: HttpErrorResponse) => {
                if (error.status === 404) {
                    this.loading.setError(`Document with ID "${docId}" not found.`);
                } else {
                    this.loading.setError(`Error ${error.status}: ${error.error}`);
                }
                this.loading.loading = false;
            });
        });
    }

    public imageChanged(imageUrl: string) {
        if(!this.doc.metadata) {
            this.doc.metadata = {};
        }
        this.doc.metadata["imageUrl"] = imageUrl;
    }

    public isImageFullscreen() {
        return (document as any).fullscreenElement;
    }

    public toggleImageFullscreen() {
        // Use this.divRef.nativeElement here to request fullscreen
        const elem = this.imageRef.nativeElement;

        if (this.isImageFullscreen()) {
            document.exitFullscreen();
        } else {
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.msRequestFullscreen) {
                elem.msRequestFullscreen();
            } else if (elem.mozRequestFullScreen) {
                elem.mozRequestFullScreen();
            } else if (elem.webkitRequestFullscreen) {
                elem.webkitRequestFullscreen();
            }
        }
    }

    public get settingMonospace() {
        const s = this.settings.get(AnnotateComponent.SETTINGS_KEY, {});
        if ("monospace" in s) return s.monospace;
        else return false;
    }

    public set settingMonospace(val: boolean) {
        const s = this.settings.get(AnnotateComponent.SETTINGS_KEY, {});
        s.monospace = val;
        this.settings.set(AnnotateComponent.SETTINGS_KEY, s);
        this.updateMonospace(val);
    }

    private updateMonospace(val?: boolean) {
        if (val == undefined) {
            val = this.settingMonospace;
        }
        if (val) {
            this.docElem.nativeElement.classList.remove("nonmonospace");
            this.docElem.nativeElement.classList.add("monospace");
        } else {
            this.docElem.nativeElement.classList.remove("monospace");
            this.docElem.nativeElement.classList.add("nonmonospace");
        }
    }

    public showAnnotationsOf(select, user_id: string) {
        if (user_id !== null && this.changed) {
            confirm(this.dialog, "Confirm Annotation Change",
                "Warning: you have unsaved annotations that will be lost.\nContinue?").subscribe(
                    (value: boolean) => {
                        if (value) {
                            this.changed = false;
                            this.showAnnotationsOf(select, user_id);
                        } else {
                            select.value = "";
                        }
                    });
            return;
        }
        this.loading.loading = true;
        this.currentSelection.clear(true);
        this.removeAllAnnotations();
        if (user_id == null) {
            this.nerData.setAnnotations(this.myNerAnnotations);
            this.canCurrentlyAnnotate = this.canAnnotate;
        } else {
            this.nerData.setAnnotations(this.othersNerAnnotations[user_id]);
            this.canCurrentlyAnnotate = false;
        }
        this.showExistingNerAnnotations();
        this.showingAnnotationsFor = user_id;
        this.changed = false;
        this.loading.loading = false;
    }

    private wordsLoaded() {
        this.updateMonospace();
        this.wordsList.forEach((item: ElementRef, idx: number) => {
            const word = this.nerData.words[idx];
            word.elem = item.nativeElement;
            if (word.innerHTML) {
                word.elem.innerHTML = word.innerHTML;
            }
        });
        this.showExistingNerAnnotations();
    }

    public click(event: MouseEvent, word: Word) {
        if (!this.canCurrentlyAnnotate) return;
        this.mousedown(event, word);
        this.mouseup(event, word);
    }

    public contextMenu(event: MouseEvent, word: Word) {
        if (!this.canCurrentlyAnnotate) return;
        const t = (<any>word.elem)._tippy;
        console.log('context menu');
        if (t) {
            t.show();
        }
        event.preventDefault();
    }

    public mousedown(event: MouseEvent, word: Word) {
        if (!this.canCurrentlyAnnotate) return;
        if (!this.mouseDown.left(event) || this.currentSelection.contains(word)) { return; }
        if (this.currentSelection.canAdd(this.nerData, word)) {
            this.currentSelection.add(this.nerData, word);
        } else if (this.currentSelection.isEmpty()) {
            this.currentSelection.clear(true);
            this.currentSelection.start(word);
        }
    }

    public mouseover(event: MouseEvent, word: Word) {
        if (!this.canCurrentlyAnnotate) return;

        if (this.mouseOutState) {
            if (!this.mouseDown.get()) {
                if (this.currentSelection.contains(this.recentWord)) {
                    this.currentSelection.addTippy((w) => this.makeTippy(w));
                }
            }
        }
        this.mouseOutState = false;

        if (!this.mouseDown.get() || this.currentSelection.contains(word)) { return; }
        if (this.currentSelection.canAdd(this.nerData, word)) {
            this.currentSelection.add(this.nerData, word);
        }
    }

    public mouseup(event: MouseEvent, word: Word) {
        if (!this.canCurrentlyAnnotate) return;
        if (!this.mouseDown.get()) { return; }

        if (this.currentSelection.contains(word)) {
            this.currentSelection.addTippy((w) => this.makeTippy(w));
        }
    }

    public mouseout(event: MouseEvent, word: Word) {
        if (event.buttons == 1) {
            this.mouseOutState = true;
            this.recentWord = word;
        }
    }

    private makeTippy(word: Word) {
        const clone = this.popoverTemplate.nativeElement.cloneNode(true);
        const labels = clone.getElementsByTagName("mat-chip");
        for (let i = 0; i < this.availableLabels.length; i++) {
            labels[i].addEventListener("click", () => {
                const isSelection = word.elem.classList.contains("select");
                if (isSelection) {
                    const words = this.currentSelection.clear(false);
                    this.setLabel(words, this.availableLabels[i]);
                } else {
                    for (const annotation of this.nerData.annotationsWith(word)) {
                        const words = this.nerData.wordsIn(annotation);
                        this.setLabel(words, this.availableLabels[i]);
                    }
                }
                const t = (<any>word.elem)._tippy;
                if (t) {
                    t.hide();
                }
            });
        }
        clone.getElementsByTagName("button")[0].addEventListener("click", () => {
            const isSelection = word.elem.classList.contains("select");
            if (isSelection) {
                this.currentSelection.clear(true);
            } else {
                for (const annotation of this.nerData.annotationsWith(word)) {
                    this.removeAnnotation(annotation);
                }
            }
        });
        clone.hidden = false;
        return {
            content: clone,
            arrow: true,
            placement: "bottom",
            trigger: "manual",
            interactive: true,
            animation: "perspective",
            inertia: true,
            theme: "light-border"
        };
    }

    private getDocLabel(label: string) {
        for (const l of this.availableLabels) {
            if (l.name === label) {
                return l;
            }
        }
    }

    private getWordColor(word: Word) {
        const colors = [];
        for (const annotation of this.nerData.annotationsWith(word)) {
            colors.push(this.getDocLabel(annotation.label).color);
        }
        if (colors.length === 0) {
            return "white";
        } else if (colors.length === 1) {
            return colors[0];
        } else {
            let ret = "linear-gradient(";
            for (let i = 0; i < colors.length; i++) {
                if (i > 0) { ret += ", "; }
                ret += colors[i];
            }
            ret += ")";
            return ret;
        }
    }

    public getColorFor(label: string) {
        return this.getDocLabel(label).color;
    }

    public getWordTooltip(word: Word) {
        return this.nerData.annotationsWith(word).map((annotation) => annotation.label).join(", ");
    }

    private setLabel(words: Word[], label: DocLabel) {
        if (words.length === 0) { return; }
        const annotation = <NerAnnotation>{
            start: words[0].start,
            end: words[words.length - 1].end,
            label: label.name
        };
        const changed = this.nerData.addOrUpdateAnnotation(annotation);
        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            if (i === 0) {
                word.elem.classList.add("annotationLeft");
            }
            word.elem.classList.add("annotation");
            if (i === words.length - 1) {
                word.elem.classList.add("annotationRight");
            }
            word.elem.style.background = this.getWordColor(word);
        }
        if (changed) {
            this.changed = true;
            this.nerData.emitChanged();
        }
    }

    private showExistingNerAnnotations() {
        for (const annotation of this.nerData.annotations) {
            const label = this.getDocLabel(annotation.label);
            const words = this.nerData.wordsIn(annotation);
            this.setLabel(words, label);
            for (const word of words) {
                tippy(word.elem, this.makeTippy(word));
            }
        }
        this.nerData.emitChanged();
    }

    private removeAllAnnotations() {
        for (const word of this.nerData.words) {
            word.elem.classList.remove("annotationLeft");
            word.elem.classList.remove("annotationRight");
            word.elem.classList.remove("annotation");
            const t = (<any>word.elem)._tippy;
            if (t) {
                t.destroy();
            }
            word.elem.style.background = "white";
        }
        this.nerData.removeAllAnnotations();
        this.nerData.emitChanged();
    }

    public removeAnnotation(annotation: NerAnnotation) {
        const words = this.nerData.wordsIn(annotation);
        const changed = this.nerData.removeAnnotation(annotation);
        if (changed) {
            this.changed = true;
            for (let i = 0; i < words.length; i++) {
                const word = words[i];
                const otherAnnotations = this.nerData.annotationsWith(word);
                if (otherAnnotations.length === 0) {
                    word.elem.classList.remove("annotationLeft");
                    word.elem.classList.remove("annotationRight");
                    word.elem.classList.remove("annotation");
                    const t = (<any>word.elem)._tippy;
                    if (t) {
                        t.destroy();
                    }
                } else if (i === 0) {
                    // remove left unless it's the left of another annotation
                    let isLeft = false;
                    for (const a of otherAnnotations) {
                        if (word.start === a.start) {
                            isLeft = true;
                            break;
                        }
                    }
                    if (!isLeft) {
                        word.elem.classList.remove("annotationLeft");
                    }
                } else if (i === words.length - 1) {
                    // remove right unless  it's the right of another annotation
                    let isRight = false;
                    for (const a of otherAnnotations) {
                        if (word.end === a.end) {
                            isRight = true;
                            break;
                        }
                    }
                    if (!isRight) {
                        word.elem.classList.remove("annotationRight");
                    }
                }
                word.elem.style.background = this.getWordColor(word);
            }
            this.nerData.emitChanged();
        }
    }

    public save(andAdvance: boolean) {
        if (!this.canAnnotate) { return; }
        const docAnnotations = [];
        for (const annotation of this.myDocAnnotations) {
            if (annotation.checked) {
                docAnnotations.push(annotation.label.name);
            }
        }
        this.error.clear();
        this.annotations.saveAnnotations(this.doc._id, docAnnotations, this.nerData.annotations).subscribe((id: string) => {
            this.myNerAnnotations = this.nerData.annotations;
            this.changed = false;
            this.events.showUserMessage.emit("Document annotations were " + (id ? "" : "NOT ") + "successfully updated.");
            if(id) {
                this.annotatedService.changeDocumentStatus({collection_id: this.doc.collection_id, doc_id: this.doc._id})
                this.iaa_reporting.createIAAReport(this.doc.collection_id).toPromise().then((res) => {
                    console.log(res);
                });
            }
            if(id && andAdvance) {
                this.advanceToNext();
            }
        }, (error: HttpErrorResponse) => {
            this.error.showHttp(error, "saving annotations");
        });
    }

    private advanceToNext() {
        this.error.clear();
        this.pipelines.advanceToNextDocumentForClassifier(this.classifier._id, this.doc._id).subscribe((success: boolean) => {
            if (success) {
                this.pipelines.getNextDocumentIdForClassifier(this.classifier._id).subscribe((documentId: string) => {
                    if (documentId != null) {
                        this.loading.loading = true;
                        this.router.navigate([`/${PATHS.document.annotate}`, documentId]);
                    } else {
                        // go back to collection details
                        this.events.showUserMessage.emit("Finished annotating all documents!");
                        this.router.navigate([`/${PATHS.collection.details}`, this.collection._id]);
                    }
                }, (error: HttpErrorResponse) => {
                    this.error.showHttp(error, "advancing to next document");
                });
            } else {
                this.error.showHtml("Unable to advance to next document.");
            }
        }, (error: HttpErrorResponse) => {
            this.error.showHttp(error, "advancing to next document");
        });
    }

}
