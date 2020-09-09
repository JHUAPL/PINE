import { Injectable } from "@angular/core";
import { Router } from "@angular/router";

import { Observable, forkJoin } from "rxjs";

import { BackendService } from "../backend/backend.service";

import { LoginComponent } from "../../component/login/login.component";

import { AppConfig } from "../../app.config";
import { PATHS } from "../../app.paths";

import { AuthModule } from "./auth-module";
import { VegasAuthModule } from "./modules/vegas-auth-module";
import { EveAuthModule } from "./modules/eve-auth-module";

import { LoginForm } from "../../model/login";
import { User, UserDetails } from "../../model/user";

@Injectable()
export class AuthService {
    
    public module: AuthModule = null;
    public moduleName: string = null;
    public loggedInUser: User = null;

    public flat: boolean;
    public canManageUsers: boolean;
    
    constructor(private backend: BackendService,
                private router: Router,
                private appConfig: AppConfig) {
    }
    
    public instantiate(): Observable<string> {
        return new Observable((observer) => {
            forkJoin([this.getModule(),
                      this.getFlat(),
                      this.getBackendLoggedInUser(),
                      this.getCanManageUsers()]).subscribe(([module,
                                                                 flat,
                                                                 user,
                                                                 canManageUsers]) => {
                this.moduleName = module;
                this.flat = flat;
                this.canManageUsers = canManageUsers;
                this.loggedInUser = user;
                if(module === VegasAuthModule.NAME) {
                    this.module = new VegasAuthModule(this.backend, this, this.router);
                    observer.next(module);
                    observer.complete();
                } else if(module === EveAuthModule.NAME) {
                    this.module = new EveAuthModule(this.backend, this, this.router);
                    (<EveAuthModule>this.module).reloadAllUsers().subscribe(() => {
                        observer.next(module);
                        observer.complete();
                    }, (error) => {
                        observer.error(error);
                        observer.complete();
                    });
                } else {
                    observer.error(`Unknown auth module: ${module}`);
                    observer.complete();
                }
            }, (error) => {
                observer.error(error);
                observer.complete();
            });
        });
    }
    
    public updateLoggedInUser(): Observable<any> {
        return new Observable<any>((observer) => {
            this.getBackendLoggedInUser().subscribe((user: User) => {
                this.loggedInUser = user;
                observer.next();
                observer.complete();
            }, (error) => {
                observer.error(error);
                observer.complete();
            });
        });
    }
    
    private getBackendLoggedInUser(): Observable<User> {
        return this.backend.get<User>("/auth/logged_in_user");
    }

    private getModule(): Observable<string> {
        return this.backend.get("/auth/module");
    }

    private getFlat(): Observable<boolean> {
        return this.backend.get("/auth/flat");
    }

    private getCanManageUsers(): Observable<boolean> {
        return this.backend.get("/auth/can_manage_users")
    }

    public getLoggedInUserDetails(): Observable<UserDetails> {
        return this.backend.get("/auth/logged_in_user_details");
    }

//    public getAllUsers(): Observable<User[]> {
//        return this.canManageUsers ? this.module.getAllUsers() : null;
//    }

    public isAuthenticated(): boolean {
        return this.loggedInUser != null;
    }

    public getLoginForm(): Observable<LoginForm> {
        return this.backend.get<LoginForm>("/auth/login_form");
    }

    public checkBackend(returnTo: string): Observable<boolean> {
        return new Observable((observer) => {
            this.getBackendLoggedInUser().subscribe((user: User) => {
                this.loggedInUser = user;
                this.router.navigate([returnTo]);
                observer.next(true);
                observer.complete();
            }, (_) => {
                observer.next(false);
                observer.complete();
            });
        });
    }

    public login(values, returnTo: string, component: LoginComponent) {
        this.module.login(values, returnTo, component);
    }

    public logout() {
        this.backend.post("/auth/logout").subscribe(() => {
            this.loggedInUser = null;
            this.router.navigate(["/login"]);
        });
    }

    public getUserDisplayName(user_id: string): string {
        return this.module.getUserDisplayName(user_id);
    }

}
