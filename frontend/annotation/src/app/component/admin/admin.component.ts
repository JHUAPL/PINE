/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit } from "@angular/core";

import { AuthService } from "../../service/auth/auth.service";

import { PATHS } from "../../app.paths";

@Component({
    selector: "app-admin",
    templateUrl: "./admin.component.html",
    styleUrls: ["./admin.component.css"]
})
export class AdminComponent implements OnInit {
    
    public static readonly SUBTITLE = "Admin Dashboard";

    public readonly PATHS = PATHS;

    constructor(public auth: AuthService) { }
    
    ngOnInit() {
    }
    
}
