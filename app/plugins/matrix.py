import asyncio
import json
import nio
import os
import safer
import sys

import app.plugin
from app.config import config
from app.data import data


class matrix(app.plugin.plugin):
    """
    Plugin to act as matrix bot and post message on state change
    """

    # Required configuration values
    _configRequired = [
        'homeserver',
        'username',
        'password',
        'room',
    ]

    # Matrix API instances
    __matrixApi = {}

    # Event loop
    __loop = None

    def __init__(self):
        """
        Constructor

        Start base class constructor and initiate connection
        """

        # Start base class constructor
        try:
            super().__init__()
        except LookupError as e:
            print(e)
            raise e

        # Init required for matrix api instances
        for host, hostConfig in self._config.items():

            # Set default session cache file
            if 'sessioncache' not in hostConfig:
                hostConfig['sessioncache'] = 'config/cache/matrix-%s' % host

            # Initialize matrix api instance and connect to server
            self.__loop = asyncio.get_event_loop()
            self.__loop.run_until_complete(self.__connect(host, hostConfig))

    def __del__(self):
        """
        Destructor to cleanup matrix api instances
        """
        for host, _ in self._config.items():
            try:
                print("MATRIX: Close connection for %s" % host)
                self.__loop.run_until_complete(self.__matrixApi[host].close())
            except KeyError:
                pass

    async def __connect(self, host, hostConfig):
        """Login to matrix using cached session information or credentials

        Parameters
        ----------
        host : string
            hostname of spacestatus-server instance
        hostConfig : dict
            configuration for plugin
        """

        if os.path.exists(hostConfig['sessioncache']):

            # Use previus session tokens
            with open(hostConfig['sessioncache'], 'r') as f:
                sessionCache = json.load(f)

            # Reauthenticate if homeserver and username are equal
            if (sessionCache['homeserver'] == hostConfig['homeserver']
                    and sessionCache['user_id'] == hostConfig['username']):

                print(
                    'MATRIX: Try reauthentication to homeserver for %s' % host
                )

                client = nio.AsyncClient(hostConfig['homeserver'])
                client.restore_login(
                    user_id=sessionCache['user_id'],
                    device_id=sessionCache['device_id'],
                    access_token=sessionCache['access_token']
                )

                self.__matrixApi[host] = client

                # Try to send welcome message to verify cached credentials
                if await self.__sendWelcomeMessage(host, hostConfig['room']):
                    return

        print('MATRIX: Authenticate to homeserver for %s' % host)

        # Try to login
        client = nio.AsyncClient(
                    hostConfig['homeserver'],
                    hostConfig['username']
                 )
        loginResponse = await client.login(
                            hostConfig['password'],
                            device_name='spacestatus-server'
                        )

        # check that we logged in succesfully
        if (isinstance(loginResponse, nio.LoginResponse)):
            print(
                'MATRIX: Successfully authenticated to ' +
                'homeserver for %s with device id %s.' %
                (host, loginResponse.device_id)
            )
            self.__matrixApi[host] = client

            with safer.open(hostConfig['sessioncache'], 'w') as f:
                f.write(
                    json.dumps(
                        {
                            "homeserver": hostConfig['homeserver'],
                            "user_id": loginResponse.user_id,
                            "device_id": loginResponse.device_id,
                            "access_token": loginResponse.access_token
                        },
                        indent=4
                    )
                )
            print('MATRIX: Save cached session for %s.' % host)
        else:
            print(
                'ERROR: Login to homeserver for %s failed: %' %
                (host, loginResponse),
                file=sys.stderr
            )
            await client.close()

        # Try to send welcome message to verify login
        if await self.__sendWelcomeMessage(host, hostConfig['room']):
            return

    async def __sendWelcomeMessage(self, host, room: str) -> bool:
        """Send welcome message with current status

        Parameters
        ----------
        host : string
            hostname of spacestatus-server instance
        room : string
            room id

        Returns
        -------
        bool
        """
        # Set welcome phrase to name and state
        welcomePhrase = \
            "Spacestatus started for %s. Current status is %s." % (
                data().getSpace(host),
                "OPEN" if data().getStateOpen(host) else "CLOSED"
            )

        # Try to join new room and haven't joined as that user, you can use
        # Joining if already joined will also be successfull
        joinResponse = await self.__matrixApi[host].join(room)
        if not isinstance(joinResponse, nio.JoinResponse):
            # Join to channel failed
            self.__matrixApi.pop(host)
            print(
                'ERROR: Matrix join to room %s for %s failed.' %
                (room, host),
                file=sys.stderr
            )
            return False

        # Push status message to matrix
        messageResponse = await self.__matrixApi[host].room_send(
            room,
            message_type="m.room.message",
            content={
                "msgtype": "m.notice",
                "body": welcomePhrase
            }
        )

        if isinstance(messageResponse, nio.RoomSendResponse):
            print('MATRIX: Welcome message for %s send successfully.' % host)
            return True
        else:
            # Cached session credetials invalid,
            # remove instance and output error message
            self.__matrixApi.pop(host)
            print(
                'ERROR: Matrix cached session for %s is not valid.' %
                (host),
                file=sys.stderr
            )
            return False

    def __getMatrixApi(self) -> nio.AsyncClient:
        """Get Matrix api instance for current host of the request

        Returns
        -------
        bool
        """
        try:
            return self.__matrixApi[self._getHost()]
        except KeyError:
            return None

    def __getRoom(self) -> str:
        """Get room id for current host of the request

        Returns
        -------
        string
        """
        return self._getConfig()['room']

    async def __onStateOpenChangeAsync(self, stateOpen: bool) -> bool:
        """Send status message async

        Parameters
        ----------
        stateOpen : bool
            current status

        Returns
        -------
        bool
        """

        # Set phrase to name and state
        phrase = \
            "%s is %s." % (
                data().getSpace(self._getHost()),
                "open" if stateOpen else "closed"
            )

        # Push status message to matrix
        messageResponse = await self.__getMatrixApi().room_send(
            self.__getRoom(),
            message_type="m.room.message",
            content={
                "msgtype": "m.notice",
                "body": "%s" % phrase
            }
        )

        if isinstance(messageResponse, nio.RoomSendResponse):
            print(
                'MATRIX: Send message "%s" for host %s successfull.' %
                (phrase, self._getHost())
            )
            return True
        else:
            # Error sending message
            print(
                'ERROR: Send status message to Matrix for %s failed: %s' %
                (self._getHost(), messageResponse),
                file=sys.stderr
            )
            return False

    def onStateOpenChange(self, stateOpen: bool):
        """Post state change on matrix room

        Parameters
        ----------
        stateOpen : bool
            new state after state change
        """

        # No matrix API instance available
        if self.__getMatrixApi() is None:
            return

        # Send message async
        self.__loop.run_until_complete(
            self.__onStateOpenChangeAsync(stateOpen)
        )
