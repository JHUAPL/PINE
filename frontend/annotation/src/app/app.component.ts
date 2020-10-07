// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { AppConfig } from "./app.config";
import { HttpErrorResponse } from "@angular/common/http";
import { Router, ActivatedRoute, NavigationEnd } from "@angular/router";
import { Title } from '@angular/platform-browser';
import { MatSnackBar } from '@angular/material';

import { Observable } from 'rxjs';
import { filter, map, switchMap } from 'rxjs/operators';

import { AuthService } from "./service/auth/auth.service";
import { EventService } from "./service/event/event.service";
import { StatusBarService } from "./service/status-bar/status-bar.service";

import { StatusBarComponent } from "./component/status-bar/status-bar.component";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit, AfterViewInit {

    isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
        .pipe(map(result => result.matches));

    public ready = false;

    public backendError = false;

    public backendErrorMessage = "";

    public title: string = 'PINE';

    @ViewChild(StatusBarComponent)
    public statusBar: StatusBarComponent;

    constructor(private titleService: Title, private router: Router, private route: ActivatedRoute,
                private breakpointObserver: BreakpointObserver,
                public appConfig: AppConfig, private authService: AuthService,
                private event: EventService, private snackBar: MatSnackBar,
                private statusBarService: StatusBarService) {
    }

    public ngOnInit() {
        localStorage.clear();
        this.authService.instantiate().subscribe((name: string) => {
            console.log(`Using auth module ${name}`);
                this.ready = true;
        }, (error: HttpErrorResponse) => {
            this.backendError = true;
            this.backendErrorMessage = error.error;
        });
        this.router.events.pipe(
            filter((event) => event instanceof NavigationEnd),
            map(() => this.route),
            map(route => route.firstChild),
            switchMap((route) => route.data),
            map((data) => {
                if(data && data["title"]) {
                    return data["title"];
                } else if(data && data["subtitle"]) {
                    return this.appConfig.appName + ": " + data["subtitle"];
                } else {
                    return this.appConfig.appName;
                }
            })
        ).subscribe((title) => {
            this.titleService.setTitle(title);
        });
        this.event.showUserMessage.subscribe((message: string) => {
            console.log("Showing user message: " + message);
            this.snackBar.open(message, "Close", {
                duration: 3000
            });
        });
        this.event.logout.subscribe(() => {
            this.logout();
        });
    }

    ngAfterViewInit() {
        this.statusBarService.component = this.statusBar;
    }

    public getLoggedIn(): boolean {
        return this.authService.isAuthenticated();
        //return this.authService.getLocalLoggedInUser() != null;
    }

    public getLoggedInUserString() {
        if(this.authService.loggedInUser != null) {
            return this.authService.loggedInUser.display_name;
        } else {
            return "<UNKNOWN>";
        }
    }

    public logout(): void {
        this.authService.logout();
        this.router.navigate([this.appConfig.loginPage]);
    }

}
