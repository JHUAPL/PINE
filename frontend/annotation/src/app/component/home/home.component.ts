import { Component, OnInit } from "@angular/core";

import { PATHS } from "../../app.paths";

@Component({
    selector: "app-home",
    templateUrl: "./home.component.html",
    styleUrls: ["./home.component.css"]
})
export class HomeComponent implements OnInit {
    
    public readonly PATHS = PATHS;
    
    constructor() { }
    
    ngOnInit() {
        
    }
    
}
