import { Injectable } from "@angular/core";
import { ActivatedRouteSnapshot, CanActivate, CanActivateChild, Router, RouterStateSnapshot } from "@angular/router";

import { AuthService } from "./auth.service";

import { AppConfig } from "../../app.config";
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable()
export class AuthGuard implements CanActivate, CanActivateChild {

    constructor(private authService: AuthService,
        private router: Router,
        private appConfig: AppConfig) { }

    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> | boolean {
        if (this.authService.isAuthenticated()) {
            return true;
        } else {
            return this.authService.isAuthenticatedObs().pipe(map((isAuth) => {
                if (!isAuth) {
                    if (state.url === "/" || "") {
                        this.router.navigate([this.appConfig.loginPage], { queryParams: { returnUrl: this.appConfig.landingPage } });
                    } else {
                        this.router.navigate([this.appConfig.loginPage], { queryParams: { returnUrl: state.url } });
                    }
                }
                return isAuth;
            }));
        }
    }

    canActivateChild(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> | boolean {
        return this.canActivate(route, state);
    }
}

@Injectable()
export class AdminAuthGuard implements CanActivate, CanActivateChild {

    constructor(private authService: AuthService,
        private router: Router,
        private appConfig: AppConfig) { }

    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
        if (this.authService.flat) {
            return false;
        } else if (this.authService.isAuthenticated()) {
            return this.authService.loggedInUser.is_admin;
        } else {
            if (state.url === "/" || "") {
                this.router.navigate([this.appConfig.loginPage], { queryParams: { returnUrl: this.appConfig.landingPage } });
            } else {
                this.router.navigate([this.appConfig.loginPage], { queryParams: { returnUrl: state.url } });
            }
        }
        return false;
    }

    canActivateChild(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
        return this.canActivate(route, state);
    }
}
