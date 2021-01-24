import connexion
import flask
import flask_executor
import inspect
import pkgutil
import os

import app.plugin


class pluginCollection:
    """
    plugin collection to scan for plugins and realise hooks

    Implentation based on
    https://www.guidodiepen.nl/2019/02/implementing-a-simple-plugin-framework-in-python/
    """

    # Singleton instance
    __instance = None

    # Plugins package module identifier
    __pluginsPackage = 'app.plugins'

    # Plugin object cache
    __plugins = []

    # Scanned paths
    __scannedPaths = []

    # Flask-Executor instance
    __executor = None

    def __new__(singletonClass):
        """Instantiate singleton class"""
        if singletonClass.__instance is None:
            print('Initialize plugins...')
            singletonClass.__instance = \
                super(pluginCollection, singletonClass).__new__(singletonClass)
            singletonClass.__instance.__reloadPlugins()
        return singletonClass.__instance

    def __reloadPlugins(self):
        """Reset the list of all plugins and initiate all available plugins"""
        self.__plugins = []
        self.__scannedPaths = []
        # print('Looking for plugins under package %s' % self.__pluginsPackage)
        self.__scanPlugins(self.__pluginsPackage)

    def __scanPlugins(self, package):
        """Recursively walk the supplied package to retrieve all plugins"""

        # Import package from parameters
        importedPackage = __import__(package, fromlist=['test'])

        # Scan all plugins in package
        for _, pluginname, ispkg in \
                pkgutil.iter_modules(
                    importedPackage.__path__,
                    importedPackage.__name__ + '.'
                ):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=['test'])
                classmembers = \
                    inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in classmembers:
                    # Only add classes that are a sub class
                    # of plugin, but NOT plugin itself
                    if (
                        issubclass(c, app.plugin.plugin) and
                        c is not app.plugin.plugin
                            ):
                        print('  Found plugin %s...' % c.__name__)
                        self.__plugins.append(c())

        # Scan all modules in current package recursively
        if isinstance(importedPackage.__path__, str):
            allCurrentPaths = [importedPackage.__path__]
        else:
            allCurrentPaths = [x for x in importedPackage.__path__]

        # Scan all paths for packages
        for packagePath in allCurrentPaths:
            if packagePath not in self.__scannedPaths:
                self.__scannedPaths.append(packagePath)

                # Get all subdirectory of the current package path directory
                childPackages = \
                    [p for p in os.listdir(packagePath)
                     if os.path.isdir(os.path.join(packagePath, p))]

                # For each subdirectory, apply the
                # __scanPlugins method recursively
                for childPackage in childPackages:
                    self.__scanPlugins(package + '.' + childPackage)

    def __prepareExecutor(self):
        if self.__executor is None:
            self.__executor = flask_executor.Executor(flask.current_app)

    def onStateOpenChange(self, stateOpen: bool):
        """
        Run plugin functions on state chage
        """
        # Prepare Executor
        self.__prepareExecutor()

        # Get requested host
        host = connexion.request.headers['Host']

        for plugin in self.__plugins:
            executorName = '%s-%s' % (host, plugin.getName())

            if (
                self.__executor.futures._state(executorName) is None or
                self.__executor.futures._state(executorName) == 'FINISHED'
               ):
                self.__executor.futures.pop(executorName)
                self.__executor.submit_stored(
                    executorName,
                    plugin.onStateOpenChange,
                    stateOpen
                )
                print(
                    'onStateOpenChange - %s for %s started.'
                    % (plugin.getName(), host)
                )
            else:
                print(
                    'ERROR: onStageChange - %s for %s already running.'
                    % (plugin.getName(), host)
                )
