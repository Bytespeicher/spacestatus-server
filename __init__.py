import connexion
import errno
import sys

from flask_cors import CORS

from app.config import config
from app.data import data
from app.pluginCollection import pluginCollection
import app.templateFilters as templateFilters


def initApp() -> connexion:
    """
    Initialize Connexion/Flask Application

    Returns
    -------
    connexion
        Connexion app instance
    """

    # Create the application instance
    app = connexion.App("Hackspace Status API", specification_dir='./')

    # Read the openapi yaml file to configure the endpoints
    app.add_api('api/openapi3.yaml', options={"swagger_ui": False})

    # Add CORS support
    CORS(app.app)

    # Initialize own jinja2 filters
    templateFilters.initialize(app)

    # Initialize plugins
    try:
        pluginCollection()
    except LookupError:
        sys.exit(errno.EINTR)

    print('Hackspace Status API started successfully')
    return app


if __name__ == '__main__':
    # Start application directly if we're running in stand alone mode
    initApp().run(host='0.0.0.0', port=5000, debug=True, threaded=True)
else:
    # Start application and set app context for running on wsgi servers
    app = initApp()
