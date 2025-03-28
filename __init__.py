import connexion
import errno
import sys

from flask_cors import CORS

import app
import app.templateFilters

from app.config import config
from app.data import data
from app.pluginCollection import pluginCollection


def error404(
        request: connexion.lifecycle.ConnexionRequest, exc: Exception
        ) -> connexion.lifecycle.ConnexionResponse:
    return \
        connexion.lifecycle.ConnexionResponse(
            status_code=404,
            body="The resource requested could not be found.",
            headers={"Content-Type": "text/plain"}
        )


def initApp() -> connexion:
    """
    Initialize Connexion/Flask Application

    Returns
    -------
    connexion
        Connexion app instance
    """

    print('%s v%s starting...' % (app.__name__, app.__version__))

    # Create the application instance
    flaskApp = connexion.FlaskApp(app.__name__, specification_dir='./')

    # Read the openapi yaml file to configure the endpoints
    flaskApp.add_api(
        'api/openapi3.yaml',
        swagger_ui_options=connexion.options.SwaggerUIOptions(swagger_ui=False)
    )

    # Add error handler for HTTP 404
    flaskApp.add_error_handler(404, error404)

    # Add ContextMiddleware (required to get hostname on api auth)
    flaskApp.add_middleware(
        connexion.middleware.context.ContextMiddleware,
        position=connexion.middleware.MiddlewarePosition.BEFORE_SECURITY
    )

    # Add CORS support
    CORS(flaskApp.app)

    # Initialize own jinja2 filters
    app.templateFilters.initialize(flaskApp)

    # Initialize plugins
    try:
        pluginCollection()
    except LookupError:
        sys.exit(errno.EINTR)

    print('%s v%s started successfully' % (app.__name__, app.__version__))
    return flaskApp


if __name__ == '__main__':
    # Start application directly if we're running in stand alone mode
    initApp().run(host='0.0.0.0', port=5000)
else:
    # Start application and set app context for running on wsgi servers
    app = initApp()
