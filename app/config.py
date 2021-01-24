import os
import pydeepmerge
import sys
import yaml


class config:
    """Data ORM for config"""

    # Singleton instance
    __instance = None

    # Data in memory
    __config = {}

    def __new__(singletonClass):
        """Instantiate singleton class"""
        if singletonClass.__instance is None:
            print('Initialize config orm object...')
            singletonClass.__instance = \
                super(config, singletonClass).__new__(singletonClass)
            singletonClass.__load(
                    singletonClass.__instance,
                    'config/config.yaml'
            )
        return singletonClass.__instance

    def __load(self, filename: str):
        """Load and check configuration from yaml file

        Parameters
        ----------
        filename : str
            Filename of the yaml configuration file
        """

        configErrors = False

        # Read configuration from yaml file
        with open(filename, 'r') as configfile:
            self.__config = yaml.load(configfile, Loader=yaml.FullLoader)

        # Test if at least one host is defined
        if 'hosts' not in self.__config or self.__config['hosts'] is None:
            print("Configcheck: No hosts defined", file=sys.stderr)
            configErrors = True

        # Test host configuration
        for host, hostdata in self.__config['hosts'].items():

            # file parameter is mandatory
            if 'file' not in hostdata:
                print(
                    "Configcheck: API json file for %s not defined" % host,
                    file=sys.stderr
                )
                configErrors = True
            # file must exist
            elif not os.path.isfile("config/apidata/%s" % hostdata['file']):
                print(
                    "Configcheck: API file for %s did not exist" % host,
                    file=sys.stderr
                )
                configErrors = True

            # key parameter is mandatory
            if 'key' not in hostdata:
                print(
                    "Configcheck: API key for %s not defined" % host,
                    file=sys.stderr
                )
                configErrors = True

        # Stop if any error occured
        if configErrors:
            sys.exit(1)

    def getConfig(self) -> dict:
        return self.__config

    def getPluginConfig(self, plugin: str) -> dict:
        pluginHostConfig = {
            k: (v['plugins'][plugin] if plugin in v['plugins'] else {})
            for k, v in self.__config['hosts'].items()
        }

        try:
            pluginConfig = self.__config['plugins'][plugin]
        except KeyError:
            pluginConfig = {}

        for host, hostConfig in pluginHostConfig.items():
            pluginHostConfig[host] = pydeepmerge.deep_merge(
                pluginConfig, hostConfig
            )

        return pluginHostConfig

    def getHostfiles(self) -> dict:
        """Get dict of hosts (key) with hostfile (value)

        Returns
        -------
        dict
            Hosts with hostfile
        """
        return {k: v['file'] for k, v in self.__config['hosts'].items()}

    def getHostfile(self, hostname: str) -> str:
        """Get hostfile for hostname

        Returns
        -------
        str
            Filename for hostname
        """
        return self.__config['hosts'][hostname]['file']

    def getKey(self, host: str) -> str:
        """Get api key for a host

        Parameters
        ----------
        host : str
            Hostname

        Returns
        -------
        dict
            Hosts with hostfile
        """
        return self.__config['hosts'][host]['key']
