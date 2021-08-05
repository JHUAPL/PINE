/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */
import { Component, OnInit, ViewChild } from "@angular/core";
import { MatDialog } from "@angular/material/dialog";
import { MatSort } from "@angular/material/sort";
import { MatTableDataSource } from "@angular/material/table";
import { FormBuilder, FormGroup, FormControl, FormArray, Validators, ValidationErrors, AbstractControl } from "@angular/forms";
import { HttpErrorResponse } from "@angular/common/http";

import { PATHS } from "../../app.paths";

import { confirm } from "../message.dialog/message.dialog.component";

import { AdminService } from "../../service/admin/admin.service";
import { AuthService } from "../../service/auth/auth.service";
import { EventService } from "../../service/event/event.service";

import { EveUser } from "../../model/user";
import { CreatedObject } from "../../model/created";
import { ValidatorFn } from "@angular/forms";

@Component({
    selector: "app-admin-users",
    templateUrl: "./admin-users.component.html",
    styleUrls: ["./admin-users.component.css"]
})
export class AdminUsersComponent implements OnInit {

    public static readonly SUBTITLE = "Manage Users";

    public readonly PATHS = PATHS;

    public loading = true;
    public loggedInId: string;

    public displayedColumns: string[] = ["id", "username", "first_name", "last_name", "actions"];
    public existingUsers: MatTableDataSource<EveUser>;
    public userHadError = false;
    public userError: string;

    public newUserForm: FormGroup;
    public submittedNewUser = false;
    public newUserHadError = false;
    public newUserError: string;

    @ViewChild(MatSort) sort: MatSort;

    constructor(private admin: AdminService, private auth: AuthService,
                private events: EventService, private formBuilder: FormBuilder,
                private dialog: MatDialog) { }

    ngOnInit() {
        this.loading = true;
        if(!this.auth.canManageUsers) return;
        this.loggedInId = this.auth.loggedInUser.id;
        this.newUserForm = this.formBuilder.group({
            id: [{value: "", disabled: false}, Validators.required],
            email: [{value: "", disabled: false}, Validators.compose([
                Validators.required, Validators.email])],
            firstname: [{value: "", disabled: false}, Validators.required],
            lastname: [{value: "", disabled: false}, Validators.required],
            description: [{value: "", disabled: false}],
            is_admin: [{value: "", disabled: false}],
            passwd: [{value: "", disabled: false}, Validators.required]
        });
        this.reload();
    }

    public reload() {
        this.loading = true;
        this.admin.getAllUsers().subscribe(
            (users: EveUser[]) => {
                this.existingUsers = new MatTableDataSource(users);
                this.existingUsers.sort = this.sort;
                this.loading = false;
            }
        );
    }

    get n() { return this.newUserForm.controls; }

    public createNewUser() {
        this.submittedNewUser = true;

        if(this.newUserForm.invalid) {
            return;
        }

        const new_user = {
            "id": this.n.id.value,
            "email": this.n.email.value,
            "firstname": this.n.firstname.value,
            "lastname": this.n.lastname.value,
            "description": this.n.description.value,
            "role": this.n.is_admin.value ? ["user", "administrator"] : ["user"],
            "passwd": this.n.passwd.value
        };
        this.newUserHadError = false;
        this.admin.addUser(new_user).subscribe(
            (createdObject: CreatedObject) => {
                // reload users service so that the new data is in there
                this.auth.module.reloadAllUsers().subscribe(() => {
                    this.newUserForm.reset();
                    this.newUserForm.markAsUntouched();
                    Object.keys(this.n).forEach((name) => {
                        const control = this.n[name];
                        control.setErrors(null);
                    });
                    this.reload();
                    this.events.showUserMessage.emit("Successfully created user with ID " + createdObject._id);
                });
            },
            (error: HttpErrorResponse) => {
                console.error(error);
                this.newUserError = error.error;
                this.newUserHadError = true;
            }
        );
    }

    public deleteUser(userId) {
        confirm(this.dialog, "Confirm User Deletion",
                "Are you sure you want to delete this user?\nThis can't be undone.").subscribe(
            (value: boolean) => {
                if(value) {
                  this.userHadError = false;
                  this.userError = null;
                  this.admin.deleteUser(userId).subscribe(
                      (response) => {
                          this.events.showUserMessage.emit("Successfully deleted user with ID " + userId);
                          this.reload();
                      },
                      (error) => {
                          console.error(error);
                          this.userError = error.error;
                          this.userHadError = true;
                      }
                  );
                }
            }
        );
    }

}
