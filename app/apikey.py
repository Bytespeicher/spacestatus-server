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
    if token != config().getKey(connexion.request.headers['Host']):
        raise connexion.exceptions.OAuthProblem('Authentication error')

    return {}
