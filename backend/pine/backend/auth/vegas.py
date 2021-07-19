# (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

from overrides import overrides

from . import oauth

# Example of user-based token for staging vegas:
#{'sub': 'lglende1', 'aud': '1976d9d4-be86-44ce-aa0f-c5a4b295c701', 'subject': 'lglende1', 'iss': 'https://slife.jh.edu', 'resource_name': 'NLP Platform', 'token_type': 'access_token', 'exp': 1622830239, 'expires_in': 3600, 'client_name': 'NLP Platform', 'iat': 1622826639, 'email': 'laura.glendenning@jhu.edu', 'client_id': '1976d9d4-be86-44ce-aa0f-c5a4b295c701'}

# Example of user-based token for prod vegas:
#{'sub': 'lglende1', 'aud': 'b7590f07-cbd9-48b1-82f4-8aab02470831', 'subject': 'lglende1', 'iss': 'https://my.jh.edu', 'resource_name': 'NLP Platform', 'token_type': 'access_token', 'exp': 1622834772, 'expires_in': 3600, 'client_name': 'NLP Platform', 'iat': 1622831172, 'email': 'laura.glendenning@jhu.edu', 'client_id': 'b7590f07-cbd9-48b1-82f4-8aab02470831'}

# Example of application-based token for staging vegas:
#{"sub": "1976d9d4-be86-44ce-aa0f-c5a4b295c701", "aud": "1976d9d4-be86-44ce-aa0f-c5a4b295c701", "iss": "https://slife.jh.edu", "resource_name": "NLP Platform", "token_type": "access_token", "exp": 1623096567, "client_name": "NLP Platform", "iat": 1623094767, "client_id": "1976d9d4-be86-44ce-aa0f-c5a4b295c701"}
#{"sub": "b8946ec1-7c8b-4e8f-8da3-033bd8c3a500", "aud": "1976d9d4-be86-44ce-aa0f-c5a4b295c701", "iss": "https://slife.jh.edu", "resource_name": "NLP Platform", "token_type": "access_token", "exp": 1622826907, "client_name": "pm-cda-projection", "iat": 1622825107, "client_id": "b8946ec1-7c8b-4e8f-8da3-033bd8c3a500"}

class VegasAuthModule(oauth.OAuthModule):
    
    def __init__(self, app, bp):
        super(VegasAuthModule, self).__init__(app, bp, app.config.get("VEGAS_CLIENT_SECRET"))
    
    @overrides
    def register_oauth(self, oauth, app):
        server = app.config.get("VEGAS_SERVER")
        return oauth.register(
            name = "vegas",
            client_id = app.config.get("VEGAS_CLIENT_ID"),
            client_secret = app.config.get("VEGAS_CLIENT_SECRET"),
            access_token_url = None,
            access_token_params = None,
            refresh_token_url = app.config.get("VEGAS_ACCESS_TOKEN_URL", "{}/VEGAS/oauth/token".format(server)),
            authorize_url = app.config.get("VEGAS_AUTHORIZE_URL", "{}/VEGAS/oauth/authorize".format(server)),
            api_base_url = app.config.get("VEGAS_API_BASE_URL", "{}/VEGAS/api/".format(server)),
            client_kwargs = None
        )
        #VEGAS_LOGOUT = VEGAS_SERVER +'/VEGAS/saml/logout'

    @overrides
    def get_login_form_button_text(self):
        return "Login With JHED"

    @overrides
    def make_user(self, decoded: dict) -> oauth.OAuthUser:
        if "subject" in decoded: # user-based token
            return oauth.OAuthUser(decoded, id_field="sub")
        else: # application-based token
            return oauth.OAuthUser(decoded, id_field="sub", display_field="client_name")
