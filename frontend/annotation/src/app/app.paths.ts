// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

export const PATHS = {
    home: "home",
    collection: {
        add: "collection/add",
        details: "collection/details",
        view: "collections"
    },
    document: {
        add: "document/add",
        annotate: "annotate"
    },
    user: {
        account: "account",
        login: "login",
        oauth: {
            authorize: "oauth/authorize"
        }
    },
    admin: {
        dashboard: "admin",
        users: "admin/users",
        modify_user: "admin/user",
        data: "admin/data"
    },
    classifier: {
      metrics: "classifier/metrics"
    }
};

export const PARAMS = {
    collection: {
        details: {
            collection_id: "collection_id"
        }
    },
    document: {
        add: {
            collection_id: "collection_id"
        },
        annotate: {
            document_id: "document_id"
        }
    },
    admin: {
        modify_user: {
            user_id: "user_id"
        }
    },
    classifier: {
        metrics: {
            classifier_id: "classifier_id"
        }
    }
};
