# pylint: disable=missing-docstring, logging-format-interpolation, invalid-name
from __future__ import absolute_import, division
import urllib
import json
import logging
from pylru import lrudecorator
from lib.barzer import barzer_objects

from config import BarzerSettings


class BarzerError(Exception):
    """ barzer access exception """


class Barzer(object):
    """ entity extraction layer """
    def __init__(self, cache_size=10):
        def make_instance_url(url, key):
            return '{}?key={}'.format(url, key)

        self.url = {k: make_instance_url(v['url'], v['key']) for k, v in BarzerSettings.BARZER_INSTANCES.iteritems()}

    def get_url(self, query, instance=None):
        """
        Args:
            query (string) - text ofthe query
            instance (string) - id of the instance
        """
        instance = instance or 'default'
        prefix_url = self.url.get(instance)
        if not prefix_url:
            logging.error('invalid barzer instance {} passed'.format(instance))
            if prefix_url != 'default':
                prefix_url = self.url['default']
            else:
                raise BarzerError('no instances found')

        return '{}&query={}'.format(prefix_url, urllib.quote(query))

    def get_json(self, query, instance=None):
        url = self.get_url(query=query, instance=instance)
        try:
            response = urllib.urlopen(url)
        except Exception as ex:  # pylint: disable=broad-except
            return {'error': 'request {} failed with error: {}'.format(url,
                                                                       str(ex))}
        return json.loads(response.read())

    @lrudecorator(100)
    def get_beads(self, query, instance=None):
        data = self.get_json_cached(query, instance)
        return barzer_objects.BeadFactory.make_beads_from_barz(data)

barzer = Barzer()
