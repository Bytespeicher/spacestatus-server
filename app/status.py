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
            data=data().get(connexion.request.headers['Host'], True)
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
            etag=True,
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


def __updateTemperature(host: str, body: dict):
    """Update sensor temperature data

    Parameters
    ----------
    body : dict
        Received api data
    """
    try:
        if len(body['sensors']['temperature']) > 0:
            data().setSensorsTemperature(
                host,
                body['sensors']['temperature']
            )
        else:
            data().removeSensorsTemperature(host)
    except KeyError:
        pass


def set(body: dict):
    """Set data received by api

    Parameters
    ----------
    body : dict
        Received api data
    """
    # Get requested host
    host = connexion.request.headers['Host']

    # Update current sensor people data
    data().setSensorsPeople(host, body['sensors']['people_now_present'])

    # Update current sensor temperature data
    __updateTemperature(host, body)

    # Update open state if changes
    if (data().getStateOpen(host) != body['state']['open']):
        data().setStateOpen(host, body['state']['open'])
        # Run plugin hook
        pluginCollection().onStateOpenChangeForHost(
            host, body['state']['open']
        )

    # Update or remove state message
    try:
        data().setStateMessage(host, body['state']['message'])
    except KeyError:
        data().setStateMessage(host, None)

    data().setStateLastchange(host, body['state']['lastchange'])
    data().commit(host)

    return connexion.NoContent, 200


def setTemperature(body: dict):
    """Set data received by api

    Parameters
    ----------
    body : dict
        Received api data
    """
    # Get requested host
    host = connexion.request.headers['Host']

    # Update current sensor temperature data
    __updateTemperature(host, body)

    data().commit(host)

    return connexion.NoContent, 200
