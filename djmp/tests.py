from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from .views import tileset_status, seed
from .models import Tileset
from mapproxy_config import get_cache_config
import os

class DjmpTest(TestCase):

    fixtures = ['test_data.json']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        self.client = Client()

    def test_seeding(self):
        """ test seeding"""
        self.client.login(username='admin', password='admin')
        resp = self.client.get(reverse('tileset_seed', args=(1,)))
        self.assertEqual('{"status": "started"}', resp.content)

    def test_mapproxy_cache_url(self):
        cache = get_cache_config()
        self.assertEqual(type(cache), tuple)

        self.assertEqual(cache[0], "file")
        self.assertEqual(len(cache), 2)
        self.assertEqual(type(cache[1]), str)

        cache = get_cache_config("file:/tmp/test/")
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache[0], "file")
        self.assertEqual(cache[1], "/tmp/test/")

        cache = get_cache_config("s3:/tmp/test/:s3-bucket-name")
        self.assertEqual(len(cache), 3)
        self.assertEqual(cache[0], "s3")
        self.assertEqual(cache[1], "/tmp/test/")
        self.assertEqual(cache[2], "s3-bucket-name")

        try:
            get_cache_config("badidea")
            self.fail("Exception should be raise")
        except ValueError:
            pass