/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

const collection_title = "NER Test Collection";
const document_fragments = [
  "Thousands of demonstrators",
  "The step will allow the",
  "Local news reports said at"
];

function goToCollection(collection_title) {
  cy.get(".doc-collections-btn")
    .should("be.visible")
    .click();
  cy.contains(collection_title)
    .should("be.visible")
    .click();
  return cy.get(".title-tabs")
    .contains("Details")
    .should("be.visible")
    .click().then(_ => {
      cy.contains("Collection title", {timeout: 20 * 1000})
        .should("be.visible")
    	.parents("tr")
    	.children("td").eq(1)
    	.should("be.visible", {timeout: 20 * 1000})
    	.should($td => {
    	  expect($td.text()).to.eq(collection_title);
    	}, {timeout: 20 * 1000});
      return cy.contains("Collection ID")
        .should("be.visible")
        .parents("tr")
        .children("td").eq(1)
        .should("be.visible")
        .invoke("text");
    });
}

function goToDocument(collection_title, document_fragment) {
  return goToCollection(collection_title).then(collection_id => {
    expect(collection_id).to.be.a("string");
    expect(collection_id.length).to.be.at.least(1);
    cy.get(".title-tabs")
      .contains("Documents")
      .should("be.visible")
      .click();
    cy.get(".doc-list-table")
      .find("table.mat-table")
      .then(table => {
        cy.wrap(table).find("td")
          .contains(document_fragment)
          .click({ force: true });
      });
    var document_id;
    cy.get(".title-toolbar-button")
      .contains("Details")
      .should("be.visible")
      .click().then(deets => {
        cy.wrap(deets).get("table")
          .get("tr")
          .contains("Document ID")
          .should("be.visible")
          .parents("tr")
          .children("td").eq(1)
          .should("be.visible")
          .then($td => {
            document_id = $td.text();
            expect(document_id).to.be.a("string");
            expect(document_id.length).to.be.at.least(1);
          });
        cy.wrap(deets).get("table")
          .get("tr")
          .contains("Collection")
          .scrollIntoView()
          .should("be.visible")
          .parents("tr")
          .children("td").eq(1)
          .should("be.visible")
          .then($td => {
            expect($td.text()).to.contain(collection_title);
            expect($td.text()).to.contain(collection_id);
          });
      	});
    cy.location().should((loc) => {
      expect(loc.pathname).to.eq(`/collection/annotate/${document_id}`);
    });
    return document_id;
  });
}

function annotateWord(wordSubject, label) {
  return wordSubject.click().then($word => {
    cy.wrap($word)
      .should("have.class", "select")
      .should("have.class", "selectLeft")
      .should("have.class", "selectRight")
      .should("not.have.class", "annotation")
      .should("not.have.class", "annotationLeft")
      .should("not.have.class", "annotationRight")
      .rightclick().then(_ => {
        cy.get("div.tippy-content")
          .find("mat-chip-list")
          .should("exist")
          .find("mat-chip")
          .contains(label)
          .should("be.visible")
          .click().then($label => {
        cy.wrap($word)
          .should("not.have.class", "select")
          .should("not.have.class", "selectLeft")
          .should("not.have.class", "selectRight")
          .should("have.class", "annotation")
          .should("have.class", "annotationLeft")
          .should("have.class", "annotationRight");
        cy.get("@annotations")
          .scrollIntoView()
          .find("tbody")
          .find("tr")
          .should("have.length", 1)
          .first()
          .should("be.visible")
          .children("td")
          .should("have.length", 5)
          .then($tds => {
            // first column: text, should be the same as the word we clicked
          cy.wrap($tds[0]).should("have.text", $word.text());
          // second column: label, should be the same as the label we clicked
          cy.wrap($tds[1]).invoke("text").then((text) => { expect(text.trim()).to.equal($label.text().trim()) });
          // third column: start, should match the class of the word we clicked
          cy.wrap($tds[2]).should("have.text", $word.attr("word-start"));
          // fourth column: end, should match the class of the word we clicked
          cy.wrap($tds[3]).should("have.text", $word.attr("word-end"));
          });
          });
      });
  });
}

function unannotateWord(wordSubject) {
  return wordSubject
    .should("have.class", "annotation")
    .should("have.class", "annotationLeft")
    .should("have.class", "annotationRight")
    .rightclick().then($word => {
      cy.get("div.tippy-content")
        .find("button")
        .contains("Remove")
        .should("be.visible")
        .click().then(_ => {
          cy.wrap($word)
            .should("not.have.class", "annotation")
            .should("not.have.class", "annotationLeft")
            .should("not.have.class", "annotationRight");
          cy.get("@annotations")
            .scrollIntoView()
            .find("tbody")
            .find("tr")
            .should("have.length", 0);
          });
    });
}

function save() {
  return cy.get(".annotate-button")
    .click().then(_ => {
      cy.get("snack-bar-container")
        .should("be.visible")
        .then($el => {
          expect($el.text()).to.contain("Document annotations were successfully updated.")
        });
      });
}

describe("Documents Tests", function() {

  it("Checks Documents are Visible in Collection Details Page with Eve", function() {
    cy.pine_login_eve();
    goToCollection(collection_title);
    cy.contains(collection_title)
      .should("be.visible");
    cy.get(".title-tabs")
      .contains("Documents")
      .should("be.visible")
      .click();
    cy.get(".doc-list-table")
      .find("table.mat-table")
      .then(table => {
        for(const frag of document_fragments) {
          cy.wrap(table).find("td")
            .contains(frag)
            .should("exist");
        }
      });
    cy.pine_logout();
  });
  
  it("Checks Annotate Page with Eve", function() {
    cy.pine_login_eve();
    const frag = document_fragments[0];
    goToDocument(collection_title, frag);
    cy.get(".title-toolbar-button")
      .contains("Details")
      .should("exist");
    cy.get("mat-panel-title")
      .contains("Document Details")
      .should("exist");
    cy.get(".title-toolbar-button")
      .contains("Image")
      .should("exist");
    cy.get("mat-panel-title")
      .contains("Image")
      .should("exist");
    cy.get(".title-toolbar-button")
      .contains("Labeling")
      .should("exist");
    cy.get("mat-panel-title")
      .contains("Document Labeling")
      .should("exist");
    cy.get(".title-toolbar-button")
      .contains("Document")
      .should("exist")
      .click();
    cy.wait(1000);
    cy.get(".mat-title")
      .contains("NER Annotations")
      .should("exist");
    cy.get(".mat-title")
      .contains("Annotation List")
      .should("exist");
    cy.get("#doc")
      .should(($doc) => {
        expect($doc).to.contain(document_fragments[0]);
      });
    cy.pine_logout();
  });

  it("Annotates an Unannotated Document with Eve", function() {
    cy.pine_login_eve();
    goToCollection(collection_title);
    cy.get(".title-tabs")
      .contains("Documents")
      .should("be.visible")
      .click();
    // find the first unannotated document
    cy.get(".doc-list-table")
      .find("table.mat-table")
      .find("mat-icon")
      .contains("clear")
      .first()
      .should("exist")
      .click({ force: true });

    cy.get("app-ner-annotation-table")
      .find("table")
      .should("exist")
      .as("annotations");
    cy.get("#doc").as("doc");
    
    // make sure the annotations table is empty
    cy.get("@annotations")
      .children()
      .should("be.empty");
    
    // annotate first word with the first label
    cy.get("@doc")
      .children("span").eq(0)
      .scrollIntoView()
      .should("be.visible")
      .should("not.have.class", "select")
      .should("not.have.class", "annotation")
      .as("firstWord");
    cy.get(".title-toolbar-button")
      .contains("Labeling")
      .should("be.visible")
      .click();
    cy.wait(1000);
    cy.get(".doc-labeling-container")
      .find("mat-chip")
      .first()
      .then($firstLabel => {
        cy.get(".title-toolbar-button")
        .contains("Document")
        .should("be.visible")
        .click();
        cy.wait(1000);
        annotateWord(cy.get("@firstWord"), $firstLabel.text().trim());
      });

    save();

    // remove annotation
    unannotateWord(cy.get("@firstWord"));

    save();

    cy.pine_logout();
  });
});
