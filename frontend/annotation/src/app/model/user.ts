// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

export interface User {
    id: string;
    username: string;
    display_name: string;
    is_admin: boolean;
}

export interface UserDetails {
    first_name: string;
    last_name: string;
    description: string;
}

export interface EveUser {
    _id: string;
    firstname: string;
    lastname: string;
    email: string;
    description: string;
    role: string[];
    passwdhash: string;
    _updated: Date;
    _created: Date;
    _etag: string;
}

//export function getUserDisplayName(user: AuthUser): string {
//    return user.name + " (" + user.username + ")";
//}
//
//export interface IUser {
//    username: string;
//    admin: boolean;
//    sub: string;
//    roles: any;
//  }
//
//export class User implements IUser {
//    userId: string;
//    email: string;
//    password: string;
//    firstName: string;
//    lastName: string;
//    admin: boolean;
//    roles: any;
//    sub: string;
//    username: string;
//  }
//
//export interface TUser {
//    aud: string;
//    client_id: string;
//    email: string;
//    exp: number;
//    iat: number;
//    iss: string;
//    sub: string;
//    subject: string;
//    token_type: string;
//    scope: any;
//}