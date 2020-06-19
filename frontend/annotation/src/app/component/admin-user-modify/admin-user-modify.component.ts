/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit } from "@angular/core";
import { ActivatedRoute, Router } from "@angular/router";
import { FormBuilder, FormGroup, FormControl, FormArray, Validators, ValidationErrors, AbstractControl } from "@angular/forms";
import { HttpErrorResponse } from "@angular/common/http";

import { PATHS, PARAMS } from "../../app.paths";

import { AdminService } from "../../service/admin/admin.service";
import { AuthService } from "../../service/auth/auth.service";
import { EventService } from "../../service/event/event.service";

import { EveUser } from "../../model/user";
import { CreatedObject } from "../../model/created";

@Component({
    selector: "app-admin-user-modify",
    templateUrl: "./admin-user-modify.component.html",
    styleUrls: ["./admin-user-modify.component.css"]
})
export class AdminUserModifyComponent implements OnInit {

    public static readonly SUBTITLE = "Modify User";

    public readonly PATHS = PATHS;

    public loading = true;

    public user: EveUser;
    public userIsMe: boolean;

    public userForm: FormGroup;
    public submittedUser = false;
    public userHadError = false;
    public userError: string;

    public passwordForm: FormGroup;
    public submittedPassword = false;
    public passwordHadError = false;
    public passwordError: string;

    constructor(private route: ActivatedRoute, private router: Router,
                private formBuilder: FormBuilder,
                private admin: AdminService,
                private auth: AuthService,
                private events: EventService) { }

    ngOnInit() {
        this.loading = true;
        this.route.paramMap.subscribe((res) => {
            const userId = res.get(PARAMS.admin.modify_user.user_id);
            this.userIsMe = userId === this.auth.loggedInUser.id;
            this.admin.getUser(userId).subscribe(
                (user: EveUser) => {
                    this.user = user;
                    this.userForm = this.formBuilder.group({
                        id: [{value: this.user._id, disabled: true}],
                        email: [{value: this.user.email, disabled: true}],
                        firstname: [{value: this.user.firstname, disabled: false}, Validators.required],
                        lastname: [{value: this.user.lastname, disabled: false}, Validators.required],
                        description: [{value: this.user.description, disabled: false}],
                        role_user: [{value: this.user.role.includes("user"), disabled: false}],
                        // don't let the current admin unmake themselves an admin
                        role_admin: [{value: this.user.role.includes("administrator"), disabled: this.userIsMe}],
                        passwdhash: [{value: this.user.passwdhash, disabled: true}]
                    });
                    this.passwordForm = this.formBuilder.group({
                        new_password: [{value: "", disabled: false}, Validators.required],
                        new_password_confirm: [{value: "", disabled: false}, Validators.required]
                    });
                    this.loading = false;
                }
            );
        });
    }

    get f() { return this.userForm.controls; }

    get p() { return this.passwordForm.controls; }

    public save() {
        this.submittedUser = true;

        if(this.userForm.invalid) {
            return;
        }

        const updatedUser = <EveUser>Object.assign({}, this.user);
        updatedUser.firstname = this.f.firstname.value;
        updatedUser.lastname = this.f.lastname.value;
        updatedUser.description = this.f.description.value;
        updatedUser.role = [];
        if(this.f.role_user.value) {
            updatedUser.role.push("user");
        }
        if(this.f.role_admin.value) {
            updatedUser.role.push("administrator");
        }

        this.userHadError = false;
        this.userError = null;
        this.admin.updateUser(this.user._id, updatedUser).subscribe(
            (created: CreatedObject) => {
                this.admin.getUser(this.user._id).subscribe(
                    (user: EveUser) => {
                        this.user = user;
                        this.auth.module.reloadAllUsers().subscribe(() => {
                            this.submittedUser = false;
                            this.events.showUserMessage.emit("Successfully updated user with ID " + this.user._id);
                        });
                });
            }, (error: HttpErrorResponse) => {
                this.userHadError = true;
                this.userError = error.error;
            }
        );
    }

    public changePassword() {
        this.submittedPassword = true;

        if(this.passwordForm.invalid) {
            return;
        }

        const new_password = this.p.new_password.value;
        const new_password_confirm = this.p.new_password_confirm.value;
        if(new_password !== new_password_confirm) {
            this.p.new_password_confirm.setErrors({"nonmatching": true});
            return;
        }

        this.passwordHadError = false;
        this.passwordError = null;
        this.admin.changeUserPassword(this.user._id, new_password).subscribe(
            (created: CreatedObject) => {
                this.admin.getUser(this.user._id).subscribe(
                    (user: EveUser) => {
                        this.user = user;
                        this.f.passwdhash.setValue(this.user.passwdhash);
                        this.submittedPassword = false;
                        this.passwordForm.reset();
                        this.passwordForm.markAsUntouched();
                        Object.keys(this.p).forEach((name) => {
                            const control = this.p[name];
                            control.setErrors(null);
                        });
                        this.events.showUserMessage.emit("Successfully updated password for user with ID " + this.user._id);
                    });
            },
            (error: HttpErrorResponse) => {
                this.passwordError = error.error;
                this.passwordHadError = true;
            }
        );
    }

}
