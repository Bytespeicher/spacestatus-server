import connexion
import flask
import os

from app.data import data


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


def json() -> dict:
    """Response the request for /status.json with the complete api output.

    Returns
    -------
    dict
        Dictionary with all api data for the requested host
    """
    return data().get(connexion.request.headers['Host'])


def set(received: dict):
    """Set data received by api

    Parameters
    ----------
    received : dict
        Received api data
    """
    # Get requested host
    host = connexion.request.headers['Host']

    # Update current sensor data
    data().setSensorsPeople(host, received['sensors']['people_now_present'])
    if 'temperature' in received['sensors']:
        data().setSensorsTemperature(host, received['sensors']['temperature'])
    else:
        data().removeSensorsTemperature(host)

    # Update open state if changes
    if (data().getStateOpen(host) != received['state']['open']):
        data().setStateOpen(host, received['state']['open'])

    data().setStateLastchange(host, received['state']['lastchange'])
    data().commit(host)

    return connexion.NoContent, 200
