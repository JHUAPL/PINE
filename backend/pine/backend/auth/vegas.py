# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from overrides import overrides

from . import oauth

#VEGAS_SERVER = "https://slife.jh.edu"
#VEGAS_CLIENT_ID = "1976d9d4-be86-44ce-aa0f-c5a4b295c701"
#VEGAS_LOGOUT = VEGAS_SERVER +'/VEGAS/saml/logout'
#VEGAS_AUTHORIZE_URL = "{}/VEGAS/oauth/authorize".format(VEGAS_SERVER)
#VEGAS_ACCESS_TOKEN_URL = "{}/VEGAS/api/oauth2/token".format(VEGAS_SERVER)

class VegasAuthModule(oauth.OAuthModule):
    
    def __init__(self, app, bp):
        super(VegasAuthModule, self).__init__(app, bp)
    
    @overrides
    def register_oauth(self, oauth, app):
        server = app.config.get("VEGAS_SERVER", "https://slife.jh.edu")
        return oauth.register(
            name = "vegas",
            client_id = app.config.get("VEGAS_CLIENT_ID", "1976d9d4-be86-44ce-aa0f-c5a4b295c701"),
            client_secret = app.config["VEGAS_CLIENT_SECRET"],
            access_token_url = None,
            access_token_params = None,
            refresh_token_url = app.config.get("VEGAS_ACCESS_TOKEN_URL", "{}/VEGAS/oauth/token".format(server)),
            authorize_url = app.config.get("VEGAS_AUTHORIZE_URL", "{}/VEGAS/oauth/authorize".format(server)),
            api_base_url = app.config.get("VEGAS_API_BASE_URL", "{}/VEGAS/oauth/".format(server)),
            client_kwargs = None
        )

    @overrides
    def get_login_form_button_text(self):
        return "Login With JHED"
