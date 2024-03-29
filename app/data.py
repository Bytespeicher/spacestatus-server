import datetime
import glob
import json
import os
import safer
import time

from app.config import config


class data:
    """Data ORM for api files"""

    # Singleton instance
    __instance = None

    # Data in memory
    __data = {}

    def __new__(singletonClass):
        """Instantiate singleton class"""
        if singletonClass.__instance is None:
            print('Initialize data orm object...')
            singletonClass.__instance = \
                super(data, singletonClass).__new__(singletonClass)
            # Autoload data files
            singletonClass.__instance.__loadFiles(config().getHostfiles())
        return singletonClass.__instance

    def __loadFiles(self, hostfiles: dict):
        """Load saved API files

        Parameters
        ----------
        config : dict
            Configuration dictionary
        """
        for host, hostfile in hostfiles.items():
            print('Load saved data for %s ...' % host)
            filename = 'config/apidata/%s' % hostfile
            with open(filename, 'r') as f:
                self.__data[host] = json.load(f)
            self.__updateStructure(host)

    def __updateStructure(self, host: str):
        """Update data structure for new version

        Parameters
        ----------
        host : str
            Hostname

        """
        # Add lastchange for temperature sensors
        try:
            test = (self.__data[host]
                    ['additional_data']['lastchange']['temperature'])
        except KeyError:
            print('Update: Add last change of temperature for %s ...' % host)
            self.__data[host].update({
                'additional_data':  {
                    'lastchange': {
                        'temperature': 0
                    }
                 }
            })

    def commit(self, host: str) -> bool:
        """Persist current API information to file

        Parameters
        ----------
        host : str
            Host to persist

        Returns
        -------
        bool
        """
        filename = 'config/apidata/%s' % config().getHostfile(host)

        with safer.open(filename, 'w') as f:
            f.write(json.dumps(self.__data[host], indent=2))
        print('Saved data for %s ...' % host)

        return True

    def get(self, host: str, includeAdditionalData: bool = False) -> dict:
        """Get full api data for host

        Parameters
        ----------
        host : str
            Hostname

        Returns
        -------
        dict
            Dictionary with api data except additional data
        """
        if host in self.__data:
            if includeAdditionalData:
                return self.__data[host]
            else:
                # Return api data from dictionary except key additional_data
                return {
                    k: self.__data[host][k]
                    for k in set(self.__data[host].keys()).difference(
                        {'additional_data'}
                    )
                }
        else:
            return {}

    def getLastModified(self, host: str) -> datetime:
        """Get datetime object for last modification

        Parameters
        ----------
        host : str
            Hostname

        Returns
        -------
        datetime
            Datetime object with last modification time
        """
        return \
            datetime.datetime.fromtimestamp(
                self.__data[host]['state']['lastchange']
            )

    def getSpace(self, host: str) -> str:
        """Get space name

        Parameters
        ----------
        host : str
            Hostname

        Returns
        -------
        str
            Name of space
        """
        return self.__data[host]['space']

    def setSensorsPeople(self, host: str, people: list):
        """Set sensor data for people

        Parameters
        ----------
        host : str
            Hostname
        people : list of dict
            List of dict with people information from hackspace api
        """
        self.__data[host]['sensors']['people_now_present'] = people

    def setSensorsTemperature(self, host: str, temperature: list):
        """Set sensor data for temperatur

        Parameters
        ----------
        host : str
            Hostname
        temperature : list of dict
            List of dict with temperature information from hackspace api
        """
        self.__data[host]['sensors']['temperature'] = temperature
        self.__data[host].update({
            'additional_data':  {
                'lastchange': {
                    'temperature': int(time.time())
                }
            }
        })

    def removeSensorsTemperature(self, host: str) -> bool:
        """Remove sensor data for temperatur

        Parameters
        ----------
        host : str
            Hostname

        Returns
        -------
        bool
            Temperature data was present and removed
        """
        try:
            self.__data[host]['sensors'].pop('temperature')
            self.__data[host]['additional_data']['lastchange'].pop(
                'temperature'
            )
        except KeyError:
            return False
            pass

        return True

    def getStateOpen(self, host: str) -> bool:
        """Get open state

        Parameters
        ----------
        host : str
            Hostname

        Returns
        -------
        bool
            Current open state
        """
        return self.__data[host]['state']['open']

    def setStateOpen(self, host: str, state: bool):
        """Set open state

        Parameters
        ----------
        host : str
            Hostname
        state : bool
            Currnt state of hackspace
        """
        self.__data[host]['state']['open'] = state

    def setStateLastchange(self, host: str, lastChange: int):
        """Set last change timestamp

        Parameters
        ----------
        host : str
            Hostname
        lastChange : int
            Timestamp of last state change
        """
        self.__data[host]['state']['lastchange'] = lastChange

    def setStateMessage(self, host: str, message: str):
        """Set state message

        Parameters
        ----------
        host : str
            Hostname
        message : str
            State message
        """
        if (message is not None):
            self.__data[host]['state']['message'] = message
        else:
            try:
                self.__data[host]['state'].pop('message')
            except KeyError:
                return False
                pass

        return True
