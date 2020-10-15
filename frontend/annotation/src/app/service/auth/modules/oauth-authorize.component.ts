import { Component, OnInit, ViewChild } from "@angular/core";
import { ActivatedRoute } from "@angular/router";

import { filter, take } from "rxjs/operators";

import { LoadingComponent } from "../../../component/loading/loading.component";

import { AuthService } from "../../../service/auth/auth.service";

import { PATHS } from "../../../app.paths";

import { OAuthModule } from "./oauth-module";

@Component({
    //selector: "app-oauth-authorize",
    templateUrl: "./oauth-authorize.component.html",
    //styleUrls: ["./login.component.css"]
})
export class OAuthAuthorizeComponent implements OnInit {
    
    public static SUBTITLE = "Authorizing...";
    
    @ViewChild(LoadingComponent)
    public loading: LoadingComponent;
    
    constructor(private route: ActivatedRoute,
                private auth: AuthService) {
        
    }
    
    ngOnInit(): void {
        this.route.queryParams.subscribe((params) => {
            this.route.fragment.subscribe((fragment) => {
              let return_to = PATHS.collection.view;
              if(params["return_to"]) {
                  return_to = params["return_to"];
              }
              this.auth.loaded$.pipe(
                filter(loaded => loaded),
                take(1)
              ).subscribe(_ => {
                (<OAuthModule>this.auth.module).authorize(params, fragment, return_to, this);
              }, (error) => {
                this.setLoginError(error);
              });
            });
        });
    }
    
    public setLoginError(error) {
        this.loading.errorMessage = error;
        this.loading.error = true;
    }
    
}
