import { Observable } from "rxjs";

import { LoginComponent } from "../../component/login/login.component";

import { User, UserDetails } from "../../model/user";

export abstract class AuthModule {
        
    public abstract login(values, returnTo: string, component: LoginComponent);
    
    public abstract getUserDisplayName(user_id: string): string;

    public reloadAllUsers(): Observable<boolean> {
        return null;
    }
    
    public getAllUsers(): Observable<User[]> {
        return null;
    }
    
    public updateLoggedInUserDetails(details: UserDetails): Observable<boolean> {
        return null;
    }
    
    public updateLoggedInUserPassword(currentPassword: string, newPassword: string): Observable<boolean> {
        return null;
    }

}
