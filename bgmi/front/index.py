# coding: utf-8
from __future__ import print_function, unicode_literals

import os
from pprint import pformat

from bgmi.config import SAVE_PATH, FRONT_STATIC_PATH
from bgmi.front.base import BaseHandler, COVER_URL
from bgmi.lib.models import STATUS_DELETED, STATUS_UPDATING, STATUS_END, Followed
from bgmi.utils import normalize_path, logger
import pymongo


def get_player(bangumi_name):
    mongoClient = pymongo.MongoClient()
    mongodb = mongoClient.get_database('bgmi')
    mongo_collection = mongodb.get_collection('bangumi')
    r = mongo_collection.find_one({'_id': bangumi_name})
    if r:
        return r['player']
    else:
        return {}


class IndexHandler(BaseHandler):
    def get(self, path):
        if not os.path.exists(FRONT_STATIC_PATH):
            msg = '''<h1>Thanks for your using BGmi</h1>
            <p>It seems you have not install BGmi Frontend, please run <code>bgmi install</code> to install.</p>
            '''
        else:
            msg = '''<h1>Thanks for your using BGmi</h1>
            <p>If use want to use Tornado to serve static files, please run 
            <code>bgmi config TORNADO_SERVE_STATIC_FILES 1</code>, and do not forget install bgmi-frontend by
            running <code>bgmi install</code></p>'''

        self.write(msg)
        self.finish()


class BangumiListHandler(BaseHandler):
    def get(self, type_=''):
        data = Followed.get_all_followed(STATUS_DELETED, STATUS_UPDATING if not type_ == 'old' else STATUS_END)

        if type_ == 'index':
            data.extend(self.patch_list)
            data.sort(key=lambda _: _['updated_time'] if _['updated_time'] else 1)

        for bangumi in data:
            bangumi['cover'] = '{}/{}'.format(COVER_URL, normalize_path(bangumi['cover']))

        data.reverse()

        for item in data:
            item['player'] = get_player(item['bangumi_name'])

        self.write(self.jsonify(data))
        self.finish()
