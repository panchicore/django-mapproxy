import logging

from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from mapproxy.seed.config import SeedConfigurationError, ConfigurationError
import helpers

from .settings import FILE_CACHE_DIRECTORY

log = logging.getLogger('djmapproxy')

CACHE_TYPES = [
    ['file', 'file'],
    #['mbtiles','mbtiles'],
    #['sqllite', 'sqllite'],
    ['gpkg', 'gpkg']
]

DIR_LAYOUTS = [
    ['tms', 'tms'],
    ['tc', 'TileCache']
]

SERVER_SERVICE_TYPES = [
    ['wms','wms'],
    ['tile', 'tile']
]

class Tileset(models.Model):

    # base
    name = models.CharField(unique=True, max_length=30)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # server
    server_url = models.URLField()
    server_service_type = models.CharField(max_length=10, choices=SERVER_SERVICE_TYPES)
    server_username = models.CharField(blank=True, max_length=30)
    server_password = models.CharField(blank=True, max_length=30)

    # layer
    layer_name = models.CharField(blank=True, max_length=200)
    layer_zoom_start = models.IntegerField(blank=True, default=0)
    layer_zoom_stop = models.IntegerField()

    # area
    bbox_x0 = models.DecimalField(max_digits=19, decimal_places=15, default=-180, validators = [MinValueValidator(-180), MaxValueValidator(180)])
    bbox_x1 = models.DecimalField(max_digits=19, decimal_places=15, default=180, validators = [MinValueValidator(-180), MaxValueValidator(180)])
    bbox_y0 = models.DecimalField(max_digits=19, decimal_places=15, default=-89.9, validators = [MinValueValidator(-89.9), MaxValueValidator(89.9)])
    bbox_y1 = models.DecimalField(max_digits=19, decimal_places=15, default=89.9, validators = [MinValueValidator(-89.9), MaxValueValidator(89.9)])

    # cache
    cache_type = models.CharField(max_length=10, choices=CACHE_TYPES)
    # file cache params
    directory_layout = models.CharField(max_length=20, choices=DIR_LAYOUTS, blank=True, null=True)
    directory = models.CharField(max_length=256, default=FILE_CACHE_DIRECTORY, blank=True, null=True)
    # gpkg cache params
    filename = models.CharField(max_length=256, blank=True, null=True)
    table_name = models.CharField(max_length=128, blank=True, null=True)

    def __unicode__(self):
        return self.name

    # terminate the seeding of this tileset!
    def stop(self):
        log.debug('tileset.stop')
        res = {'status': 'not in progress'}
        pid_str = helpers.get_pid_from_lock_file(self)
        process = helpers.get_process_from_pid(pid_str)
        if process:
            log.debug('tileset.stop, will stop, pid: {}').format(pid_str)
            res = {'status': 'stopped'}
            children = process.children()
            for c in children:
                c.terminate()
            process.terminate()
        else:
            if pid_str == 'preparing_to_start':
                res = {'status': 'debug, prevent start!'}
                # TODO: prevent it from starting!
                log.debug('process not running but may be started shortly')
            elif helpers.is_int_str(pid_str):
                log.debug('tileset.stop, process not running but cleaned lock file')

        helpers.remove_lock_file(self.id)
        return res

    def seed(self):
        
        lock_file = helpers.get_lock_file(self)
        if lock_file:
            log.debug('generating tileset')
            try:
                pid = helpers.seed_process_spawn(self)
                lock_file.write("{}\n".format(pid))
                res = {'status': 'started'}
            except (SeedConfigurationError, ConfigurationError) as e:
                log.error('Something went wrong when generating.. removing lock file')

                helpers.remove_lock_file(self)
                res = {'status': 'unable to start',
                       'error': e.message}
            finally:
                lock_file.flush()
                lock_file.close()
        else:
            log.debug('tileset.generate, will NOT generate. already running, pid: {}'.format(helpers.get_pid_from_lock_file(self)))
            res = {'status': 'already started'}

        return res