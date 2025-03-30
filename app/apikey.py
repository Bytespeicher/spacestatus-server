import connexion

from app.config import config


def auth(token: str, required_scopes=None) -> dict:
    """Check api key authentication

    Parameters
    ----------
    token : string
        Token provided via HTTP header
    required_scopes
        Scopes (not used)

    Return
    ------
    dict
        Informations about user (empty, not used)
    """
    authKey = config().getKey(connexion.request.headers['Host'])
    if (isinstance(authKey, str)):
        # Validate against single auth key
        if token == authKey:
            return {}
    elif (isinstance(authKey, dict)):
        # Validate against url rule name auth key
        try:
            if token == authKey[str(connexion.request.url.path)]:
                return {}
        except KeyError:
            pass

    # No valid key found
    raise connexion.exceptions.OAuthProblem('Authentication error')
