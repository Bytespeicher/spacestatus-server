import pydeepmerge
import random
import sys
import twitter as twitterApi

import app.plugin
from app.config import config


class twitter(app.plugin.plugin):
    """
    Plugin to post message on state change to Twitter
    """

    # Default config
    _configDefault = {
        'wordlist': {
            'name': ["The space"],
            'verb': ["is"],
            'state': {
                'open': ["open"],
                'closed': ["closed"]
            },
            'adjective': {
                'open': [],
                'closed': []
            }
        },
        'timeout': 30,
    }

    # Required configuration values
    _configRequired = [
        'access.token',
        'access.secret',
        'consumer.key',
        'consumer.secret'
    ]

    # Twitter API instances
    __twitterApi = {}

    def __init__(self):
        # Start base class constructor
        try:
            super().__init__()
        except LookupError as e:
            print(e)
            raise e

        # Init required twitter api instances
        for host, hostConfig in self._config.items():

            # Initialize twitter api instance for host
            self.__twitterApi[host] = twitterApi.Api(
                consumer_key=hostConfig['consumer']['key'],
                consumer_secret=hostConfig['consumer']['secret'],
                access_token_key=hostConfig['access']['token'],
                access_token_secret=hostConfig['access']['secret'],
                timeout=hostConfig['timeout']
            )

            # Check credentials
            try:
                verifyCredentials =\
                    self.__twitterApi[host].VerifyCredentials(
                        include_entities=False,
                        skip_status=True,
                        include_email=False
                    )
                print(
                    'Twitter: Credentials for %s on host %s verified.' %
                    (verifyCredentials.screen_name, host)
                )
            except twitterApi.error.TwitterError as e:
                # Credentials wrong, remove instance and output error message
                self.__twitterApi.pop(host)
                print(
                    'ERROR: Twitter credentials for %s are not valid: %s' %
                    (host, e),
                    file=sys.stderr
                )

    def __getWordlist(self) -> dict:
        try:
            return self._getConfig()['wordlist']
        except KeyError:
            pass

        return {}

    def __getTwitterApi(self) -> twitterApi.api:
        try:
            return self.__twitterApi[self._getHost()]
        except KeyError:
            return None

    def onStateOpenChange(self, stateOpen: bool):
        """Post state change on twitter

        Parameters
        ----------
        stateOpen : bool
            new state after state change
        """

        # No twitter API instance available
        if self.__getTwitterApi() is None:
            return

        # Get wordlist
        wordlist = self.__getWordlist()

        # Set phrase to name and verb
        phrase = \
            "%s %s " % (
                random.choice(wordlist['name']),
                random.choice(wordlist['verb'])
            )

        # Add state to phrase
        if stateOpen:
            phrase += random.choice(wordlist['state']['open']) + ". "
        else:
            phrase += random.choice(wordlist['state']['closed']) + ". "

        # Sometimes add adjective with first upper case
        if (random.choice([True, False])):
            if stateOpen:
                phrase += \
                    random.choice(
                        wordlist['adjective']['open']
                    ).title() + "!"
            else:
                phrase += \
                    random.choice(
                        wordlist['adjective']['closed']
                    ).title() + "!"

        phrase = phrase.rstrip()

        # Push status message to twitter
        try:
            self.__getTwitterApi().PostUpdate(phrase)
            print(
                'Twitter: Send message "%s" for host %s successfull.' %
                (phrase, self._getHost())
            )
        except twitterApi.error.TwitterError as e:
            # Error sending message
            print(
                'ERROR: Send status message to Twitter for %s failed: %s' %
                (self._getHost(), e),
                file=sys.stderr
            )
