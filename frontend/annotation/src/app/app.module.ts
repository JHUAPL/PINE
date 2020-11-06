// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { BrowserModule, Title } from "@angular/platform-browser";
import { NgModule, APP_INITIALIZER } from "@angular/core";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { RouterModule } from "@angular/router";
import { AppComponent } from "./app.component";
import { LayoutModule } from "@angular/cdk/layout";
import { HttpClientModule } from "@angular/common/http";
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { FlexLayoutModule } from '@angular/flex-layout';

import {
    MatAutocompleteModule,
    MatBadgeModule,
    MatBottomSheetModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatChipsModule,
    MatDatepickerModule,
    MatDialogModule,
    MatDividerModule,
    MatExpansionModule,
    MatGridListModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatMenuModule,
    MatNativeDateModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatRadioModule,
    MatRippleModule,
    MatSelectModule,
    MatSidenavModule,
    MatSliderModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatSortModule,
    MatStepperModule,
    MatTableModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    MatTreeModule,
} from "@angular/material";
import { MatCheckboxModule } from "@angular/material/checkbox";
import { Ng2PanZoomModule } from "ng2-panzoom";

import "hammerjs";

import { CookieService } from "ngx-cookie-service";

import { AppConfig } from "./app.config";
import { routing } from "./app.routing";

import { AuthService } from "./service/auth/auth.service";
import { BackendService } from "./service/backend/backend.service";
import { CollectionRepositoryService } from "./service/collection-repository/collection-repository.service";
import { DocumentRepositoryService } from "./service/document-repository/document-repository.service";
import { EventService } from "./service/event/event.service";
import { SettingsService } from "./service/settings/settings.service";

import { AuthGuard, AdminAuthGuard } from "./service/auth/auth-guard.service";

import { LoginComponent } from "./component/login/login.component";
import { AddCollectionComponent } from "./component/add-collection/add-collection.component";
import { CollectionDetailsComponent, AddLabelDialog, AddViewerDialog, AddAnnotatorDialog} from "./component/collection-details/collection-details.component";
import { AddDocumentComponent } from "./component/add-document/add-document.component";
import { ViewCollectionsComponent } from "./component/view-collections/view-collections.component";
import { UserChooserComponent } from "./component/user-chooser/user-chooser.component";
import { LabelChooserComponent } from "./component/label-chooser/label-chooser.component";
import { AdminComponent } from "./component/admin/admin.component";
import { AdminUsersComponent } from "./component/admin-users/admin-users.component";
import { AccountComponent } from "./component/account/account.component";
import { AdminUserModifyComponent } from "./component/admin-user-modify/admin-user-modify.component";
import { MessageDialogComponent } from "./component/message.dialog/message.dialog.component";
import { NERAnnotationTableComponent } from "./component/ner-annotation-table/ner-annotation-table.component";
import { AnnotateComponent } from "./component/annotate/annotate.component";
import { LoadingComponent } from "./component/loading/loading.component";
import { DocumentDetailsComponent } from "./component/document-details/document-details.component";
import { AdminDataComponent } from "./component/admin-data/admin-data.component";
import { ErrorComponent } from "./component/error/error.component";
import { OAuthAuthorizeComponent } from "./service/auth/modules/oauth-authorize.component";
import { MetricsComponent } from './component/metrics/metrics.component';
import { ConfMatrixComponent } from './component/conf-matrix/conf-matrix.component';
import { VennDiagComponent } from './component/venn-diag/venn-diag.component';
import { MetricsHistoryComponent } from './component/metrics-history/metrics-history.component';
import { CollectionIaaReportComponent } from './component/collection-iaa-report/collection-iaa-report.component';
import { IaaHeatmapComponent } from './component/iaa-heatmap/iaa-heatmap.component';
import { DownloadCollectionDataDialogComponent } from './component/download-collection-data.dialog/download-collection-data.dialog.component';
import { ImageExplorerComponent } from './component/image-explorer/image-explorer.component';
import { ImageFilterService } from './service/image/image-filter.service';
import { ImageChooserComponent, ImageChooserDialog } from './component/image-chooser/image-chooser.component';
import { ImageCollectionUploaderComponent, ImageCollectionUploaderDialog } from './component/image-collection-uploader/image-collection-uploader.component';
import { StatusBarComponent } from './component/status-bar/status-bar.component';
import { StatusBarService } from "./service/status-bar/status-bar.service";
import { AboutComponent } from './component/about/about.component';
import { ToolbarNavComponent } from './component/toolbar/toolbar-nav/toolbar-nav.component';
import { ToolbarNavButtonComponent } from './component/toolbar/toolbar-nav-button/toolbar-nav-button.component';
import { UserCardComponent } from './component/user-card/user-card.component';

export function initializeApp(appConfig: AppConfig) {
    return () => appConfig.load();
}

@NgModule({
    declarations: [
        AppComponent,
        LoginComponent,
        AddCollectionComponent,
        CollectionDetailsComponent,
        AddDocumentComponent,
        ViewCollectionsComponent,
        UserChooserComponent,
        LabelChooserComponent,
        AdminComponent,
        AdminUsersComponent,
        AccountComponent,
        AdminUserModifyComponent,
        MessageDialogComponent,
        NERAnnotationTableComponent,
        AnnotateComponent,
        LoadingComponent,
        DocumentDetailsComponent,
        AdminDataComponent,
        ErrorComponent,
        OAuthAuthorizeComponent,
        MetricsComponent,
        ConfMatrixComponent,
        VennDiagComponent,
        MetricsHistoryComponent,
        CollectionIaaReportComponent,
        IaaHeatmapComponent,
        DownloadCollectionDataDialogComponent,
        AddViewerDialog,
        AddAnnotatorDialog,
        AddLabelDialog,
        ImageExplorerComponent,
        ImageChooserComponent,
        ImageChooserDialog,
        ImageCollectionUploaderComponent,
        ImageCollectionUploaderDialog,
        StatusBarComponent,
        AboutComponent,
        ToolbarNavComponent,
        ToolbarNavButtonComponent,
        UserCardComponent
    ],
    imports: [
        BrowserModule,
        BrowserAnimationsModule,
        ReactiveFormsModule,
        FlexLayoutModule,
        LayoutModule,
        MatAutocompleteModule,
        MatBadgeModule,
        MatBottomSheetModule,
        MatButtonModule,
        MatButtonToggleModule,
        MatCardModule,
        MatCheckboxModule,
        MatChipsModule,
        MatDatepickerModule,
        MatDialogModule,
        MatDividerModule,
        MatExpansionModule,
        MatGridListModule,
        MatIconModule,
        MatInputModule,
        MatListModule,
        MatMenuModule,
        MatNativeDateModule,
        MatPaginatorModule,
        MatProgressBarModule,
        MatProgressSpinnerModule,
        MatRadioModule,
        MatRippleModule,
        MatSelectModule,
        MatSidenavModule,
        MatSliderModule,
        MatSlideToggleModule,
        MatSnackBarModule,
        MatSortModule,
        MatStepperModule,
        MatTableModule,
        MatTabsModule,
        MatToolbarModule,
        MatTooltipModule,
        MatTreeModule,
        MatCheckboxModule,
        MatTooltipModule,
        BrowserAnimationsModule,
        HttpClientModule,
        FormsModule,
        Ng2PanZoomModule,
        routing
    ],
    providers: [
        Title,
        CookieService,
        AppConfig,
        {
            provide: APP_INITIALIZER,
            useFactory: initializeApp,
            deps: [AppConfig], multi: true
        },
        AuthService,
        AuthGuard,
        AdminAuthGuard,
        BackendService,
        CollectionRepositoryService,
        DocumentRepositoryService,
        EventService,
        SettingsService,
        ImageFilterService,
        StatusBarService
    ],
    bootstrap: [AppComponent],
    entryComponents: [
        MessageDialogComponent,
        DownloadCollectionDataDialogComponent,
        AddAnnotatorDialog,
        AddLabelDialog,
        AddViewerDialog,
        ImageChooserDialog,
        ImageCollectionUploaderDialog,
        AboutComponent,
        AddCollectionComponent,
        AddDocumentComponent
    ]

})
export class AppModule { }
