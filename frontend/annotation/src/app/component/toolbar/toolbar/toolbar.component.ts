import { Component, OnInit } from '@angular/core';
import { AuthService } from 'src/app/service/auth/auth.service';

@Component({
    selector: 'app-toolbar',
    templateUrl: './toolbar.component.html',
    styleUrls: ['./toolbar.component.scss']
})
export class ToolbarComponent implements OnInit {

    title = "PMAP Data Catalog"
    //user: AuthUser;
    //faBookOpen = faBookOpen;

    constructor(private authService: AuthService) { }

    ngOnInit() {
        /* this.authService.currentUser$.subscribe((user) =>{
            this.user = user;
        }); */
    }

    logout(): void {
        this.authService.logout();
    }

}
