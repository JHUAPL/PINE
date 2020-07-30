/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ViewChild } from "@angular/core";
import { Router, ActivatedRoute } from "@angular/router";
import { FormBuilder, FormGroup, Validators } from "@angular/forms";

import { AuthService } from "../../service/auth/auth.service";

import { LoadingComponent } from "../loading/loading.component";

import { LoginFormFieldType, LoginFormField, LoginForm } from "../../model/login";

import { AppConfig } from "../../app.config";

@Component({
    selector: "app-login",
    templateUrl: "./login.component.html",
    styleUrls: ["./login.component.css"]
})
export class LoginComponent implements OnInit {

    public static readonly SUBTITLE = "Login";
    
    @ViewChild(LoadingComponent)
    public loading: LoadingComponent;

    public form: LoginForm;
    public loginForm: FormGroup;
    public submitted = false;
    public returnUrl: string;
    public loginError: string;

    constructor(private formBuilder: FormBuilder,
                private route: ActivatedRoute,
                private router: Router,
                private authService: AuthService,
                public appConfig: AppConfig) {
    }

    ngOnInit() {
        this.returnUrl = this.route.snapshot.queryParams["returnUrl"] || this.appConfig.landingPage;
        const checkBackend = "checkBackend" in this.route.snapshot.queryParams;
        if(this.isAuthenticated()) {
            this.router.navigate([this.returnUrl]);
        } else if(checkBackend) {
            this.authService.checkBackend(this.returnUrl).subscribe((loggedIn: boolean) => {
                if(loggedIn) {
                    this.router.navigate([this.returnUrl]);
                } else {
                    this.setupForm();
                }
            });
        } else {
            this.setupForm();
        }
    }

    private setupForm() {
        this.authService.getLoginForm().subscribe((form: LoginForm) => {
            this.form = form;
            let fields = {};
            for(let field of form.fields) {
                fields[field.name] = ["", Validators.required];
            }
            this.loginForm = this.formBuilder.group(fields);
            this.loading.loading = false;
        }, (error) => {
            this.loading.error = true;
            this.loading.errorMessage = `Error loading login form: ${error}.`;
            this.loading.loading = false;
        });
    }

    isAuthenticated(): boolean {
        return this.authService.isAuthenticated();
    }

    login(): void {
        this.submitted = true;
        this.loginError = null;
        if(this.loginForm.invalid) {
            return;
        }
        
        this.authService.login(this.loginForm.value, this.returnUrl, this);
    }
    
    public setLoginError(message: string) {
        this.loginError = message;
    }

    // convenience getter for easy access to form fields
    get f() { return this.loginForm.controls; }

}
