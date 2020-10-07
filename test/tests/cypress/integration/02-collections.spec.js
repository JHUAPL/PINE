/* (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC. */

function verifyCollectionDetails(collection = {
  _id: string,
  metadata: {
	title: string,
	description: string
  },
  creator_id: string,
  viewers: array,
  annotators: array
}) {
  cy.contains(collection.metadata.title)
    .should("be.visible");
  return cy.get("#metadata-table", {timeout: 20 * 1000})
    .should("be.visible")
    .then((md) => {
      const checkEquals = (key, value) => {
        cy.wrap(md).contains("td", key)
          .scrollIntoView()
          .should("be.visible")
          .parent("tr")
          .children("td").eq(1)
          .containsExactly(value)
          .should("be.visible");
      };
      const checkContains = (key, value) => {
        cy.wrap(md).contains("td", key)
          .scrollIntoView()
          .should("be.visible")
          .parent("tr")
          .children("td").eq(1)
          .contains(value)
          .should("be.visible");
      };
      const checkNonEmpty = (key) => {
        cy.wrap(md).contains("td", key)
          .scrollIntoView()
          .should("be.visible")
          .parent("tr")
          .children("td").eq(1)
          .should("not.be.empty");
      };
      const getValue = (key) => {
        return cy.wrap(md).contains("td", key)
          .scrollIntoView()
          .should("be.visible")
          .parent("tr")
          .children("td").eq(1)
          .should("not.be.empty")
          .invoke("text");
      };

      if(collection._id) {
    	checkEquals("Collection ID", collection_id);
      }
      checkEquals("Collection title", collection.metadata.title);
      if(collection.metadata.description) {
    	checkContains("Additional", collection.metadata.description);
      }
      checkNonEmpty("Collection ID");
      checkNonEmpty("Creation Date");
      checkNonEmpty("Last Updated");

      cy.request("GET", Cypress.env("API_URL") + "/auth/module").then(response => {
    	expect(response.status).to.eq(200);
    	if(response.body == "eve") {
    	  cy.fixture("users.json").then((users) => {
    		var user = users.find(u => u._id == collection.creator_id);
    	    checkContains("Creator", user.firstname);
    	    checkContains("Creator", user.lastname);
    	    checkContains("Creator", user.email);
            for(const viewer_id of collection.viewers) {
              user = users.find(u => u._id == viewer_id);
        	  checkContains("Viewers", user.firstname);
        	  checkContains("Viewers", user.lastname);
        	  checkContains("Viewers", user.email);
        	}
        	for(const annotator_id of collection.annotators) {
        	  user = users.find(u => u._id == annotator_id);
        	  checkContains("Annotators", user.firstname);
        	  checkContains("Annotators", user.lastname);
        	  checkContains("Annotators", user.email);
        	}
    	  });
    	} else {
      	  checkContains("Creator", collection.creator_id);
    	  for(const viewer_id of collection.viewers) {
    		  checkContains("Viewers", viewer_id);
    	  }
    	  for(const annotator_id of collection.annotators) {
    		  checkContains("Annotators", annotator_id);
    	  }
    	}
      });

      for(const button of ["Upload Images", "Archive", "Download Data"]) {
        cy.get("button")
          .contains(button)
          .parent("button")
          .scrollIntoView()
          .should("be.visible")
          .should("be.enabled");
      }
      
      return getValue("Collection ID");
    });
}

describe("Collections Tests", function() {

  it("Checks Collections are Visible in My Collections Page with Eve", function() {
    cy.pine_login_eve();
    cy.get(".doc-collections-btn")
      .should("be.visible")
      .click();
    cy.fixture("collections.json").then((collections) => {
      for(const data of collections) {
        const collection = data.collection;
        cy.containsElemExactly("td", collection.metadata.title)
        .should("be.visible");
      }
    });
    cy.pine_logout();
  });

  it("Checks Collection Details Page Has Metadata with Eve", function() {
    cy.pine_login_eve();
    cy.fixture("collections.json").then((collections) => {
      for(const data of collections) {
        const collection = data.collection;
        cy.get(".doc-collections-btn")
          .should("be.visible")
          .click();
        cy.containsElemExactly("td", collection.metadata.title)
          .should("be.visible")
          .click();
        cy.get(".title-tabs")
          .contains("Details")
          .should("be.visible")
          .click();
        verifyCollectionDetails(collection);
      }
    });
    cy.pine_logout();
  });

  it("Checks Adding and Archiving of a Collection with Eve", function() {
    cy.pine_login_eve();
    cy.visit("/")
    cy.contains("Add Document Collection")
      .should("be.visible")
      .click();
    cy.get("app-add-collection")
      .find("form").as("form")
      .should("be.visible");

    // make sure that required fields are checked
    cy.get("@form")
      .submit();
    cy.get("@form").within(() => {
      cy.contains("Title is required")
        .scrollIntoView()
        .should("be.visible");
      cy.contains("Description is required")
      	.scrollIntoView()
      	.should("be.visible");
      cy.contains("At least one label is required")
      	.scrollIntoView()
      	.should("be.visible");
      cy.contains("Pipeline is required")
      	.scrollIntoView()
      	.should("be.visible");
    });

    const collection = {
      metadata: {
    	title: "Testing Adding a Collection",
    	description: "This is a collection added by Cypress test."
      },
      creator_id: Cypress.env("LOGIN_USER"),
      viewers: [Cypress.env("LOGIN_USER")],
      annotators: [Cypress.env("LOGIN_USER")],
      labels: ["test"]
    };
    const csv_file = "snorkel_test.csv";
    
    // set required fields
    cy.get("@form")
      .find("input[formcontrolname='metadata_title']")
      .scrollIntoView()
      .should("be.visible")
      .type(collection.metadata.title)
      .should("have.value", collection.metadata.title);
    cy.get("@form")
      .find("textarea[formcontrolname='metadata_description']")
      .scrollIntoView()
      .should("be.visible")
      .type(collection.metadata.description)
      .should("have.value", collection.metadata.description);
    for(const label of collection.labels) {
      cy.get("@form")
        .find("app-label-chooser")
        .find("input")
        .scrollIntoView()
        .should("be.visible")
        .type(`${label}{enter}`);
      cy.get("@form")
        .find("app-label-chooser")
        .find("mat-chip-list")
        .scrollIntoView()
        .find("mat-chip")
        .should("be.visible")
        .contains(label)
        .should("be.visible");
    }
    cy.fixture("pipelines.json").then((pipelines) => {
      const pipeline = pipelines[0];
      cy.get("@form")
        .find("mat-select[formcontrolname='pipeline_id']")
        .scrollIntoView()
        .should("be.visible")
        .set_mat_select_value(pipeline.title);
    });
    cy.get("@form").within(() => {
      cy.contains("Title is required")
        .should("not.exist");
      cy.contains("Description is required")
        .should("not.exist");
      cy.contains("At least one label is required")
        .should("not.exist");
      cy.contains("Pipeline is required")
      .should("not.exist");
    });

    // attach a CSV file
    cy.get("#file_upload")
      .upload_file(csv_file, "text/csv");
    cy.get("@form")
      .find("input[formcontrolname='csv_file']")
      .scrollIntoView()
      .click()
      .should("be.visible")
      .should("have.value", csv_file);
    cy.get("@form")
      .find("mat-checkbox[formcontrolname='csv_has_header']")
      .should("be.visible")
      .should("have.class", "mat-checkbox-checked");
    cy.get("@form")
      .find("mat-select[formcontrolname='csv_text_col']")
      .should("be.visible")
      .set_mat_select_value("text");

    // create collection
    cy.get("@form")
      .submit();

    // make sure title is now listed in collection details page and in the nav menu
    cy.get(".doc-collections-btn")
      .should("be.visible")
      .click();
    cy.containsElemExactly("td", collection.metadata.title)
      .should("be.visible")
      .click();
    cy.get(".title-tabs")
        .contains("Details")
        .should("be.visible")
        .click();
    verifyCollectionDetails(collection).then(collection_id => collection._id = collection_id);
    cy.location().should((loc) => {
    	expect(loc.pathname).to.eq(`/collection/details/${collection._id}`);
    });
    
    // archive collection
    cy.get("button")
      .contains("Unarchive")
      .should("not.exist");
    cy.get("button")
      .contains("Archive")
      .click();
    cy.wait(500);
    cy.get("button")
      .contains("Unarchive")
      .should("exist");

    // make sure title is no longer listed
    cy.get(".doc-collections-btn")
      .should("be.visible")
      .click();
    cy.containsElemExactly("td", collection.metadata.title)
      .should("not.exist");

    // wait for snackbar
    cy.wait(3000);
    
    cy.pine_logout();
  });

});
