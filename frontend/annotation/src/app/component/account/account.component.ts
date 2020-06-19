/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit } from "@angular/core";
import { FormBuilder, FormGroup, FormControl, FormArray, Validators, ValidationErrors, AbstractControl } from "@angular/forms";
import { HttpErrorResponse } from "@angular/common/http";

import { AuthService } from "../../service/auth/auth.service";
import { EventService } from "../../service/event/event.service";

import { User, UserDetails } from "../../model/user";

@Component({
  selector: "app-account",
  templateUrl: "./account.component.html",
  styleUrls: ["./account.component.css"]
})
export class AccountComponent implements OnInit {

    public static SUBTITLE = "Manage Account";

    public detailsForm: FormGroup;
    public details: UserDetails;
    public submittedDetails = false;
    public detailsHadError = false;
    public detailsError: string;

    public passwordForm: FormGroup;
    public submittedPassword = false;
    public passwordHadError = false;
    public passwordError: string;

    public loading = true;

    constructor(private auth: AuthService, private event: EventService,
                private formBuilder: FormBuilder) { }

    ngOnInit() {
        this.loading = true;
        if(!this.auth.canManageUsers) {
            return;
        }
        this.passwordForm = this.formBuilder.group({
            current_password: [{value: "", disabled: false}, Validators.required],
            new_password: [{value: "", disabled: false}, Validators.required],
            new_password_confirm: [{value: "", disabled: false}, Validators.required]
        });
        this.auth.getLoggedInUserDetails().subscribe(
            (details: UserDetails) => {
                this.details = details;
                this.detailsForm = this.formBuilder.group({
                    email: [{value: this.auth.loggedInUser.id, disabled: true},
                             Validators.required],
                    first_name: [{value: this.details.first_name, disabled: false},
                                 Validators.required],
                    last_name: [{value: this.details.last_name, disabled: false},
                                Validators.required],
                    description: [{value: this.details.description, disabled: false}]
                });
                this.loading = false;
            },
            (error) => {
                console.log(error);
//                this.backendError = true;
//                this.backendErrorMessage = JSON.stringify(error);
            }
        ); 
    }

    get d() { return this.detailsForm.controls; }

    public changeDetails() {
        this.submittedDetails = true;

        if(this.detailsForm.invalid) {
            return;
        }

        const details = <UserDetails>{};
        details.first_name = this.d.first_name.value;
        details.last_name = this.d.last_name.value;
        details.description = this.d.description.value;

        this.detailsHadError = false;
        this.detailsError = null;
        this.detailsHadError = false;
        this.auth.module.updateLoggedInUserDetails(details).subscribe(
            (success: boolean) => {
                if(success) {
                    this.auth.updateLoggedInUser().subscribe(() => {
                        Object.keys(this.d).forEach(control => {
                            this.d[control].markAsPristine();
                        });
                        this.event.showUserMessage.emit("Successfully updated details.");
                    }, (error) => {
                        this.detailsHadError = true;
                        this.detailsError = JSON.stringify(error);
                    })
                } else {
                    this.detailsHadError = true;
                    this.detailsError = "Update did not succeed.";
                }
            },
            (error) => {
                this.detailsHadError = true;
                this.detailsError = JSON.stringify(error);
            }
        );
    }

    get p() { return this.passwordForm.controls; }

    public changePassword() {
        this.submittedPassword = true;

        if(this.passwordForm.invalid) {
            return;
        }

        // make sure new password and confirmation match
        const current_password = this.p.current_password.value;
        const new_password = this.p.new_password.value;
        const new_password_confirm = this.p.new_password_confirm.value;
        if(new_password !== new_password_confirm) {
            this.p.new_password_confirm.setErrors({"nonmatching": true});
            return;
        }

        this.passwordHadError = false;
        this.auth.module.updateLoggedInUserPassword(current_password, new_password).subscribe(
            (success) => {
                if(success) {
                    this.event.showUserMessage.emit("Successfully updated password.");
                    this.submittedPassword = false;
                    this.passwordForm.reset();
                    this.passwordForm.markAsUntouched();
                    Object.keys(this.p).forEach((name) => {
                        const control = this.p[name];
                        control.setErrors(null);
                    });
                } else {
                    this.passwordError = "Unknown password error.  (This shouldn't happen.)";
                    this.passwordHadError = true;
                }
            }, (error: HttpErrorResponse) => {
                console.log(error);
                this.passwordError = error.error;
                this.passwordHadError = true;
            }
        );
    }

}
