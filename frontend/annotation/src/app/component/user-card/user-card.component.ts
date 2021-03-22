import { Component, OnInit } from '@angular/core';

import { User, UserDetails } from 'src/app/model/user';
import { AuthService } from 'src/app/service/auth/auth.service';
import { PATHS } from "../../app.paths";

@Component({
    selector: 'app-user-card',
    templateUrl: './user-card.component.html',
    styleUrls: ['./user-card.component.scss']
})
export class UserCardComponent implements OnInit {

    public readonly PATHS = PATHS;

    public user: User;

    constructor(private authService: AuthService) { }

    ngOnInit() {
        this.user = this.authService.loggedInUser;
    }

    logout(): void {
        this.authService.logout();
    }
}
