/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This is will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_Expressions

Cypress.Commands.add("upload_file", {prevSubject: true}, (subject, fileName, fileType) => {
  cy.fixture(fileName, "hex").then((fileHex) => {
    const fileBytes = [];
    for(var i = 0, len = fileHex.length; i < len; i += 2) {
      fileBytes.push(parseInt(fileHex.substr(i, 2), 16));
    }
    const testFile = new File([new Uint8Array(fileBytes)], fileName, {
      type: fileType
    });
    const dataTransfer = new DataTransfer();
    const el = subject[0];

    dataTransfer.items.add(testFile);
    el.files = dataTransfer.files;
    if ("createEvent" in document) {
      var evt = document.createEvent("HTMLEvents");
      evt.initEvent("change", false, true);
      el.dispatchEvent(evt);
    } else {
      el.fireEvent("onchange");
    }
  });
});

Cypress.Commands.add("get_angular_component", {prevSubject: true}, (subject) => {
  const el = subject[0];
  const win = el.ownerDocument.defaultView; // get the window from the DOM element
  return win.ng.probe(el).componentInstance;
});

Cypress.Commands.add("set_mat_select_value", {prevSubject: true}, (subject, value) => {
  cy.wrap(subject)
    .scrollIntoView()
    .click()
    .then(_ => {
      cy.get("span.mat-option-text")
        .contains(value)
        .should("be.visible")
        .parent("mat-option")
        .click().then(() => {
          cy.wrap(subject).find("div.mat-select-value")
            .contains(value);
        });
    });
});

function exactly(value, allowWhitespace = false) {
  return new RegExp(
    "^" + (allowWhitespace ? "\\s*" : "") +
    value.replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&') + // $& means the whole matched string
    (allowWhitespace ? "\\s*" : "") + "$");
}

Cypress.Commands.add("containsExactly", {
  prevSubject: "optional"
}, (subject, content, allowWhitespace = false) => {
  return subject ? cy.wrap(subject).contains(exactly(content, allowWhitespace)) : cy.contains(exactly(content, allowWhitespace));
});

// can't use a dual function and overload containsExactly because of arguments confusion
Cypress.Commands.add("containsElemExactly", {
  prevSubject: "optional"
}, (subject, selector, content, allowWhitespace = false) => {
  return subject ? cy.wrap(subject).contains(selector, exactly(content, allowWhitespace)) : cy.contains(selector, exactly(content, allowWhitespace));
});

Cypress.Commands.add("pine_login_eve", {}, () => {
  cy.fixture("users.json").then((users) => {
    var user = users.find(u => u["_id"] == Cypress.env("LOGIN_USER") || u["email"] == Cypress.env("LOGIN_USER"));
    cy.request("POST", Cypress.env("API_URL") + "/auth/login",
      {"username": Cypress.env("LOGIN_USER"), "password": user["password"]});
    cy.visit("/login?checkBackend");
    cy.get("#toolbar")
      .contains(user["_id"])
      .should("be.visible");
  });
});

Cypress.Commands.add("pine_logout", {}, () => {
  cy.get("#pineNavLogout")
    .should("be.visible")
    .click();
  // the following check should change if auth module isn't eve
  cy.contains("Username or email")
    .should("be.visible");
});
