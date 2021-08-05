// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.
import { Routes, RouterModule } from "@angular/router";

import { PATHS, PARAMS } from "./app.paths";

import { AuthGuard, AdminAuthGuard } from "./service/auth/auth-guard.service";

import { LoginComponent } from "./component/login/login.component";
import { AddCollectionComponent } from "./component/add-collection/add-collection.component";
import { CollectionDetailsComponent } from "./component/collection-details/collection-details.component";
import { AddDocumentComponent } from "./component/add-document/add-document.component";
import { ViewCollectionsComponent } from "./component/view-collections/view-collections.component";
import { AdminComponent } from "./component/admin/admin.component";
import { AdminUsersComponent } from "./component/admin-users/admin-users.component";
import { AccountComponent } from "./component/account/account.component";
import { AdminUserModifyComponent } from "./component/admin-user-modify/admin-user-modify.component";
import { AnnotateComponent } from "./component/annotate/annotate.component";
import { AdminDataComponent } from "./component/admin-data/admin-data.component";
import { OAuthAuthorizeComponent } from "./service/auth/modules/oauth-authorize.component";

const appRoutes: Routes = [
    {path: "", redirectTo: PATHS.collection.view, pathMatch: 'full'},
    {path: PATHS.user.login, component: LoginComponent, data: { subtitle: LoginComponent.SUBTITLE }},
    {path: `${PATHS.document.annotate}/:${PARAMS.document.annotate.document_id}`, component: AnnotateComponent, canActivate: [AuthGuard],
        data: { subtitle: AnnotateComponent.SUBTITLE}},
    {path: `${PATHS.collection.details}/:${PARAMS.collection.details.collection_id}`, component: CollectionDetailsComponent, canActivate: [AuthGuard],
        data: { subtitle: CollectionDetailsComponent.SUBTITLE }},
    {path: PATHS.collection.view, component: ViewCollectionsComponent, canActivate: [AuthGuard],
        data: { subtitle: ViewCollectionsComponent.SUBTITLE }},
    {path: PATHS.user.account, component: AccountComponent, canActivate: [AuthGuard],
        data: { subtitle: AccountComponent.SUBTITLE }},
    {path: PATHS.admin.dashboard, component: AdminComponent, canActivate: [AuthGuard, AdminAuthGuard],
        data: { subtitle: AdminComponent.SUBTITLE }},
    {path: PATHS.admin.users, component: AdminUsersComponent, canActivate: [AuthGuard, AdminAuthGuard],
        data: { subtitle: AdminUsersComponent.SUBTITLE }},
    {path: `${PATHS.admin.modify_user}/:${PARAMS.admin.modify_user.user_id}`, component: AdminUserModifyComponent, canActivate: [AuthGuard, AdminAuthGuard],
        data: { subtitle: AdminUserModifyComponent.SUBTITLE }},
    {path: PATHS.admin.data, component: AdminDataComponent, canActivate: [AuthGuard, AdminAuthGuard],
        data: { subtitle: AdminDataComponent.SUBTITLE }},
    {path: PATHS.user.oauth.authorize, component: OAuthAuthorizeComponent,
        data: { subtitle: OAuthAuthorizeComponent.SUBTITLE }},
    {path: "**", redirectTo: PATHS.collection.view}
];

export const routing = RouterModule.forRoot(appRoutes, { relativeLinkResolution: 'legacy' });
