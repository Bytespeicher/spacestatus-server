import connexion
import flask
import os

from app.data import data
from app.pluginCollection import pluginCollection


def home() -> str:
    """
    Response the request for / with a rendered html page

    Returns
    -------
    string
        Rendered output of home.html
    """
    return \
        flask.render_template(
            'home.html',
            data=data().get(connexion.request.headers['Host'])
        )


def static(filetype, filename):
    """
    Response the request for /static to serve static files
    Filetype and Filename are filtered by openapi3 definition.

    Returns
    -------
    binary
        File content
    """
    response = \
        flask.send_from_directory(
            'static/%s' % filetype,
            filename,
            add_etags=True,
            conditional=True
        )
    response.direct_passthrough = False
    return response


def status() -> dict:
    """Response the request for /status.json with the complete api output.

    Returns
    -------
    dict
        Dictionary with all api data for the requested host
    """
    return data().get(connexion.request.headers['Host'])


def statusMinimal() -> dict:
    """
    Response the request for /status-minimal.json with
    a minimal status output.

    Returns
    -------
    dict
        Dictionary with minimal status data for the requested host
    """
    json = data().get(connexion.request.headers['Host'])
    minimal = {
        'open': json['state']['open'],
        'icon':
            json['state']['icon']['open']
            if json['state']['open']
            else json['state']['icon']['closed']
    }
    return minimal


def __updateTemperature(host: str, received: dict):
    """Update sensor temperature data

    Parameters
    ----------
    received : dict
        Received api data
    """
    try:
        if len(received['sensors']['temperature']) > 0:
            data().setSensorsTemperature(
                host,
                received['sensors']['temperature']
            )
        else:
            data().removeSensorsTemperature(host)
    except KeyError:
        pass


def set(received: dict):
    """Set data received by api

    Parameters
    ----------
    received : dict
        Received api data
    """
    # Get requested host
    host = connexion.request.headers['Host']

    # Update current sensor people data
    data().setSensorsPeople(host, received['sensors']['people_now_present'])

    # Update current sensor temperature data
    __updateTemperature(host, received)

    # Update open state if changes
    if (data().getStateOpen(host) != received['state']['open']):
        data().setStateOpen(host, received['state']['open'])
        # Run plugin hook
        pluginCollection().onStateOpenChange(received['state']['open'])

    # Update or remove state message
    try:
        data().setStateMessage(host, received['state']['message'])
    except KeyError:
        data().setStateMessage(host, None)

    data().setStateLastchange(host, received['state']['lastchange'])
    data().commit(host)

    return connexion.NoContent, 200


def setTemperature(received: dict):
    """Set data received by api

    Parameters
    ----------
    received : dict
        Received api data
    """
    # Get requested host
    host = connexion.request.headers['Host']

    # Update current sensor temperature data
    __updateTemperature(host, received)

    data().commit(host)

    return connexion.NoContent, 200
