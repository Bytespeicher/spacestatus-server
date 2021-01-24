import datetime


def templateStrftime(value: int, formatString: str) -> str:
    """
    Strftime filter for jinja2 to convert a unix timestamp

    Parameters
    ----------
    value : int
        Unix timestamp value
    formatString : str
        Formatstring for strftime

    Returns
    -------
    str
        Formatted Date string
    """
    return datetime.datetime.fromtimestamp(value).strftime(formatString)


def initialize(app):
    """
    Initialize jinja2 filters

    Parameters
    ----------
    app : connexion / flask
        Connexion/Flask app
    """
    app.app.jinja_env.filters['strftime'] = templateStrftime
