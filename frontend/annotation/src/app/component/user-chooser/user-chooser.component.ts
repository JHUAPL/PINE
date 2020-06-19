/*(C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

import { Component, OnInit, ElementRef, ViewChild, Input, Output, EventEmitter } from '@angular/core';
import { COMMA, ENTER, TAB } from '@angular/cdk/keycodes';
import { FormBuilder, FormGroup, FormControl, FormArray, Validators } from '@angular/forms';
import { MatAutocompleteSelectedEvent, MatChipInputEvent } from '@angular/material';
import { HttpErrorResponse } from "@angular/common/http";

import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

import { AuthService } from "../../service/auth/auth.service";

import { User } from "../../model/user";

@Component({
    selector: 'app-user-chooser',
    templateUrl: './user-chooser.component.html',
    styleUrls: ['./user-chooser.component.css']
})
export class UserChooserComponent implements OnInit {

    @Input() public requireLoggedInUser = false;
    @Input() public excludeLoggedInUser = false;
    @Input() public formFieldClass = "form-field";
    @Input() public formFieldAppearance = "standard";
    @Input() public label = "Users";

    @Output() public userAdded: EventEmitter<string> = new EventEmitter();
    @Output() public userRemoved: EventEmitter<string> = new EventEmitter();

    public loading = true;
    public hasError = false;
    public errorMessage: string;

    public users: { [id: string]: User } = {};
    public availableUserIds: string[];
    public chosenUserIds: string[] = [];
    private requiredUserIds: string[] = [];

    private separatorKeysCodes: number[] = [ENTER, COMMA, TAB];
    private filteredUserIds: Observable<string[]>;

    @ViewChild("userInput") public userInput: ElementRef;
    public userCtrl = new FormControl();

    constructor(private auth: AuthService) {
        this.filteredUserIds = this.userCtrl.valueChanges.pipe(
                startWith(null),
                map((userId: string | null) => userId ? this._filter(userId) : this.availableUserIds.slice()));
    }

    ngOnInit() {
        this.loading = true;
        this.users = {};
        this.availableUserIds = [];
        this.chosenUserIds = [];
        this.requiredUserIds = [];
        if(this.auth.canManageUsers) {
            this.auth.module.getAllUsers().subscribe((users: User[]) => {
                for(let i = 0; i < users.length; i++) {
                    const user = users[i];
                    if(this.excludeLoggedInUser && !this.requireLoggedInUser &&
                            this.auth.loggedInUser != null && this.auth.loggedInUser.id === user.id) {
                        continue;
                    }
                    this.users[user.id] = user;
                    this.availableUserIds.push(user.id);
                }
                this.sortAvailableUserIds();
                if(this.requireLoggedInUser) {
                    this.addRequiredUser(this.auth.loggedInUser.id);
                }
                this.loading = false;
            }, (error: HttpErrorResponse) => {
                this.errorMessage = error.error;
                this.hasError = true;
            });
        } else {
            if(this.requireLoggedInUser) {
                this.addRequiredUser(this.auth.loggedInUser.id);
            }
            this.loading = false;
        }
    }

    public getUserDisplayName(id: string) {
        return this.auth.getUserDisplayName(id);
    }

    public getChosenUserIds(): string[] {
        return this.chosenUserIds;
    }

    public setError(message: string) {
        this.errorMessage = message;
        this.hasError = true;
    }

    public clearError() {
        this.hasError = false;
        this.errorMessage = null;
    }

    public addRequiredUser(userId: string) {
        if(this.chosenUserIds.indexOf(userId) < 0) {
            this.chosenUserIds.push(userId);
        }
        if(this.requiredUserIds.indexOf(userId) < 0) {
            this.requiredUserIds.push(userId);
        }
        if(this.auth.canManageUsers) {
            if(this.availableUserIds.indexOf(userId) >= 0) {
                this.availableUserIds.splice(this.availableUserIds.indexOf(userId), 1);
            }
        }
    }

    private sortAvailableUserIds() {
        if(this.auth.canManageUsers) {
            this.availableUserIds.sort((a, b) => this.users[a].display_name.localeCompare(this.users[b].display_name));
        }
    }

    public userIdCanBeRemoved(userId: string): boolean {
        return this.requiredUserIds.indexOf(userId) < 0;
    }
    
    private addUserId(id: string) {
        this.userInput.nativeElement.value = "";
        this.userCtrl.setValue(null);
        if(this.auth.canManageUsers) {
            this.availableUserIds.splice(this.availableUserIds.indexOf(id), 1);
        }
        if(this.chosenUserIds.indexOf(id) < 0) {
            this.chosenUserIds.push(id);
            this.userAdded.emit(id);
        }
    }

    public selectedUser(event: MatAutocompleteSelectedEvent) {
        const id = event.option.value;
        this.addUserId(id);
    }

    public addUser(event: MatChipInputEvent) {
        // this method is called if the user pushes enter
        // right now do nothing -- may want an error or autocomplete in the future
        if(!this.auth.canManageUsers) { // we don't get the selectedUser() autocomplete event
            this.addUserId(event.value);
        }
    }

    public removeUserId(userId: string) {
        if(this.userIdCanBeRemoved(userId)) {
            if(this.auth.canManageUsers) {
                this.availableUserIds.push(userId);
                this.sortAvailableUserIds();
            }
            this.chosenUserIds.splice(this.chosenUserIds.indexOf(userId), 1);
            this.userRemoved.emit(userId);
            this.userCtrl.setValue(this.userCtrl.value);
        }
    }

    private _filter(value: string): string[] {
        if(!this.auth.canManageUsers) {
            return [];
        }
        const filterValue = value.toLowerCase();

        return this.availableUserIds.filter(userId =>
            this.users[userId].display_name.toLowerCase().indexOf(filterValue) >= 0 ||
            this.users[userId].username.toLowerCase().indexOf(filterValue) >= 0
        );
    }

}
