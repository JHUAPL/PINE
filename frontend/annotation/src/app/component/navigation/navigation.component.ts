/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, Output, EventEmitter } from "@angular/core";

import { PATHS } from "../../app.paths";
import { AppConfig } from "../../app.config";

import { AuthService } from "../../service/auth/auth.service";
import { EventService } from "../../service/event/event.service";

@Component({
  selector: "app-navigation",
  templateUrl: "./navigation.component.html",
  styleUrls: ["./navigation.component.css"]
})
export class NavigationComponent implements OnInit {

    public readonly PATHS = PATHS;

    public isExpanded = true;

    constructor(public appConfig: AppConfig, public authService: AuthService,
            private events: EventService) { }

    ngOnInit() {
    }

    public doLogout() {
        this.events.logout.emit(null);
    }

    public userIsAdmin() {
        return this.authService.loggedInUser.is_admin;
    }

}
