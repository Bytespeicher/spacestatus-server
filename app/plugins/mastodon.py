import pydeepmerge
import random
import sys
import mastodon as mastodonApi
from mastodon import Mastodon

import app.plugin
from app.config import config


class mastodon(app.plugin.plugin):
    """
    Plugin to post message on state change to Mastodon
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
    }

    # Required configuration values
    _configRequired = [
        'base_url',
        'access_token',
    ]

    # Maximum retries to post message
    __maxRetries = 3

    # Mastodon API instances
    __mastodonApi = {}

    def __init__(self):
        # Start base class constructor
        try:
            super().__init__()
        except LookupError as e:
            print(e)
            raise e

        # Init required mastodon api instances
        for host, hostConfig in self._config.items():

            # Initialize mastodon api instance for host
            self.__mastodonApi[host] = Mastodon(
                #cliend_id=hostConfig['access']['client_id'],
                #client_secret=hostConfig['access']['client_secret'],
                #access_token=hostConfig['access']['access_token'],
                access_token=hostConfig['access_token'],
                api_base_url=hostConfig['base_url']
            )

            # Check credentials
            try:
                verifyCredentials =\
                    self.__mastodonApi[host].account_verify_credentials()
                #print('DEBUG: %s' % verifyCredentials)
                print(
                    'Mastodon: Credentials for %s on server %s for %s verified.' %
                    (verifyCredentials.display_name, hostConfig['base_url'], host)
                )
            except mastodonApi.errors.MastodonError as e:
                # Credentials wrong, remove instance and output error message
                self.__mastodonApi.pop(host)
                print(
                    'ERROR: Mastodon credentials for %s are not valid: %s' %
                    (host, e),
                    file=sys.stderr
                )

    def __getWordlist(self) -> dict:
        try:
            return self._getConfig()['wordlist']
        except KeyError:
            pass

        return {}

    def __getMastodonApi(self) -> Mastodon:
        try:
            return self.__mastodonApi[self._getHost()]
        except KeyError:
            return None

    def onStateOpenChange(self, stateOpen: bool):
        """Post state change on mastodon

        Parameters
        ----------
        stateOpen : bool
            new state after state change
        """

        # No mastodon API instance available
        if self.__getMastodonApi() is None:
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

        retry = 0
        while retry < self.__maxRetries:
            # Push status message to mastodon
            try:
                self.__getMastodonApi().status_post(
                    phrase,
                    visibility='unlisted'
                )
                print(
                    'Mastodon: Send message "%s" for host %s successfull.' %
                    (phrase, self._getHost())
                )
                retry = self.__maxRetries
            except mastodonApi.error.MastodonError as e:
                # Error sending message
                print(
                    'ERROR: Send status message to Mastodon for %s failed: %s' %
                    (self._getHost(), e),
                    file=sys.stderr
                )
                retry = self.__maxRetries
            except requests.exceptions.ConnectionError as e:
                # Error sending message
                print(
                    'ERROR: Mastodon connection error for %s: %s' %
                    (self._getHost(), e),
                    file=sys.stderr
                )
                retry += 1
