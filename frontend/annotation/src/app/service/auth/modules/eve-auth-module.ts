import { Router } from "@angular/router";
import { HttpErrorResponse } from "@angular/common/http";

import { Observable } from "rxjs";

import { LoginComponent } from "../../../component/login/login.component";

import { AuthService } from "../auth.service";
import { BackendService } from "../../backend/backend.service";

import { AuthModule } from "../auth-module";

import { User, UserDetails } from "../../../model/user";

export class EveAuthModule extends AuthModule {
    
    public static NAME = "eve";
    
    private allUsers: {[s: string]: User;} = {};

    constructor(private backend: BackendService,
                private auth: AuthService,
                private router: Router) {
        super();
    }
    
    public login(values, returnTo: string, component: LoginComponent) {
        this.backend.post<User>("/auth/login", values).subscribe((user) => {
            this.auth.loggedInUser = user;
            this.router.navigate([returnTo]);
        }, (error: HttpErrorResponse) => {
            component.setLoginError(`Error logging in: ${error.error}.`);
        });
    }
    
    public getUserDisplayName(user_id: string): string {
        if(user_id in this.allUsers) {
            return this.allUsers[user_id].display_name;
        } else {
            return user_id;
        }
    }
    
    public getAllUsers(): Observable<User[]> {
        return new Observable((observer) => {
            observer.next(Object.values(this.allUsers));
            observer.complete();
        });
    }
    
    public reloadAllUsers(): Observable<any> {
        return new Observable((observer) => {
            this.backend.get<User[]>("/auth/users").subscribe((users: User[]) => {
                for(let user of users) {
                    this.allUsers[user.id] = user;
                }
                observer.next();
                observer.complete();
            }, (error) => {
                observer.error(error);
                observer.complete();
            });
        });
    }
    
    public updateLoggedInUserDetails(details: UserDetails): Observable<boolean> {
        return this.backend.post("/auth/logged_in_user_details", details);
    }
    
    public updateLoggedInUserPassword(currentPassword: string, newPassword: string): Observable<boolean> {
        const body = {
            current_password: currentPassword,
            new_password: newPassword
        };
        return this.backend.post("/auth/logged_in_user_password", body);
    }

}
