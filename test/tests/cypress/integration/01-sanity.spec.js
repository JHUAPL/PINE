/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

describe("Sanity Tests", function() {

  it("Checks Page Loads and is Eve", function() {
    cy.visit("/");
    cy.get(".login-field")
      .should("be.visible");
  });

  it("Checks Invalid Username Eve Login", function() {
    cy.visit("/");
    cy.get(".login-field")
      .should("be.visible");
    cy.get("input[name='username']")
      .should("be.visible")
      .type("BAD_USER")
      .should("have.value", "BAD_USER");
    cy.get("input[name='password']")
      .should("be.visible")
      .type("BAD_PASSWORD");
    cy.get("button")
      .should("be.visible")
      .click();
    cy.contains("Error logging in")
      .should("be.visible");
    cy.contains("User \"BAD_USER\" doesn't exist.")
      .should("be.visible");
  });

  it("Checks Invalid Password Eve Login", function() {
    cy.visit("/");
    cy.get(".login-field")
      .should("be.visible");
    cy.get("input[name='username']")
      .should("be.visible")
        .type(Cypress.env("LOGIN_USER"))
        .should("have.value", Cypress.env("LOGIN_USER"));
        cy.get("input[name='password']")
          .should("be.visible")
          .type("BAD_PASSWORD");
        cy.get("button")
          .should("be.visible")
          .click();
    cy.contains("Error logging in")
      .should("be.visible");
    cy.contains("Incorrect password for user \"" + Cypress.env("LOGIN_USER") + "\".")
      .should("be.visible");
  });

  it("Checks Valid Eve Login and Logout", function() {
    cy.fixture("users.json").then((users) => {
      var user = users.find((u) => u["_id"] == Cypress.env("LOGIN_USER") || u["email"] == Cypress.env("LOGIN_USER"));
      cy.visit("/");
      cy.get(".login-field")
        .should("be.visible");
      cy.get("input[name='username']")
        .should("be.visible")
        .type(Cypress.env("LOGIN_USER"))
        .should("have.value", Cypress.env("LOGIN_USER"));
      cy.get("input[name='password']")
        .should("be.visible")
        .type(user["password"]);
      cy.get("button")
        .should("be.visible")
        .click();
      cy.contains(Cypress.env("LOGIN_USER"))
        .should("be.visible");
      cy.pine_logout();
    });
  });

  it("Checks Valid Eve Login and Logout Through Backend", function() {
    cy.pine_login_eve();
    cy.pine_logout();
  });

  it("Checks About Dialog With Eve", {
      retries: 2,
    }, function() {
	  cy.pine_login_eve();
	  cy.visit("/");
	  cy.get(".app-toolbar")
	    .get(".info-btn")
	    .should("be.visible")
		.click();
	  cy.get("app-about")
	    .find("#content")
	    .should("be.visible")
	    .within(() => {
	    	cy.contains("PINE", {timeout: 20 * 1000})
	    	  .should("be.visible", {timeout: 20 * 1000});
	    	cy.contains("database", {timeout: 20 * 1000})
	    	  .should("be.visible", {timeout: 20 * 1000});
	    });
	  cy.get("app-about")
	    .find("button").contains("Close")
	    .should("be.visible")
	    .click();
	  cy.get(".app-toolbar")
        .get(".info-btn")
	    .should("be.visible");
	  cy.pine_logout();
  });

});
