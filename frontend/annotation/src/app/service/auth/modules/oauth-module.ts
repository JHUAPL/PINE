import { Router } from "@angular/router";

import { Observable } from "rxjs";

import { LoginComponent } from "../../../component/login/login.component";
import { OAuthAuthorizeComponent } from "./oauth-authorize.component";

import { AuthService } from "../auth.service";
import { BackendService } from "../../backend/backend.service";

import { AuthModule } from "../auth-module";

import { PATHS } from "../../../app.paths";

import { User } from "../../../model/user";

export abstract class OAuthModule extends AuthModule {
    
    constructor(private backend: BackendService,
                private auth: AuthService,
                private router: Router) {
        super();
    }
    
    public login(values, returnTo: string, component: LoginComponent) {
        let return_to = this.backend.frontendUrl(`/${PATHS.user.oauth.authorize}?return_to=${returnTo}`);
        this.backend.post<string>("/auth/login", {}, {params: {return_to: return_to}}).subscribe((redirectUrl) => {
            window.location.href = redirectUrl;
        }, (error) => {
            component.setLoginError(`Error logging in: ${error}.`);
        });
    }
    
    public authorize(params: object, fragment: string, returnTo: string, component: OAuthAuthorizeComponent) {
        this.backend.get<User>(`/auth/authorize`, {params: {...params, ...{fragment: fragment}}}).subscribe((user) => {
            this.auth.loggedInUser = user;
            this.router.navigate([returnTo]);
        }, (error) => {
            component.setLoginError(`Error logging in: ${error.error["error"]}.`);
        });
    }
    
    public getUserDisplayName(user_id: string): string {
        return user_id;
    }
    
    public getAllUsers(): Observable<User[]> { return null; }
    
}
