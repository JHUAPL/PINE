// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

// see models.py in backend

export enum LoginFormFieldType {
    TEXT = "text",
    PASSWORD = "password"
}

export interface LoginFormField {
    name: string;
    display: string;
    type: LoginFormFieldType;
}

export interface LoginForm {
    fields: LoginFormField[];
    button_text: string;
}
