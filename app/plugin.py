import connexion
import pydeepmerge
import sys

from abc import ABC, abstractmethod

from app.config import config


class plugin(ABC):
    """Abstract base class for each plugin

    All methods that all plugins must implement should be defined here

    Implentation based on
    https://www.guidodiepen.nl/2019/02/implementing-a-simple-plugin-framework-in-python/
    """

    # Configuration
    _config = {}

    # Hostname of request
    _hostname = None

    def getName(self) -> str:
        return self.__class__.__name__

    def __init__(self):
        self._loadConfig()
        try:
            self._checkConfig()
        except LookupError as e:
            raise e

    def _loadConfig(self) -> dict:
        self._config = config().getPluginConfig(self.getName())

        for host in list(self._config):

            try:
                pluginEnabled = self._config[host]['enabled']
            except KeyError:
                pluginEnabled = False

            if not pluginEnabled:
                self._config.pop(host)

        if hasattr(self, '_configDefault'):
            for host, hostConfig in self._config.items():
                self._config[host] = pydeepmerge.deep_merge(
                    self._configDefault,
                    hostConfig
                )

        return self._config

    def _checkConfig(self):

        configErrors = False

        # No configuration check required
        if not hasattr(self, '_configRequired'):
            return

        # Check configuration by host
        for host, hostConfig in self._config.items():

            # Check configuration by required values
            for configKey in self._configRequired:

                try:
                    configKey = configKey.split('.')
                    if len(configKey) == 1:
                        x = hostConfig[configKey[0]]
                    if len(configKey) == 2:
                        x = hostConfig[configKey[0]][configKey[1]]
                except KeyError:
                    print(
                        "Configcheck: [%s / %s] Key %s missing." %
                        (host, self.getName(), configKey),
                        file=sys.stderr
                    )
                    configErrors = True

        # Configuration error occured
        if configErrors:
            raise LookupError(
                    'Configuration for plugin %s not valid.' % self.getName()
            )

    def _getConfig(self) -> dict:
        return self._config[self._getHost()]

    def _setHost(self, host: str):
        self._host = host

    def _getHost(self) -> str:
        return self._host

    def onStateOpenChangeForHost(self, host: str, stateOpen: bool):
        self._setHost(host)
        self.onStateOpenChange(stateOpen)

    @abstractmethod
    def onStateOpenChange(self, host: str, stateOpen: bool):
        """The method will be executed on state change"""
        raise NotImplementedError
