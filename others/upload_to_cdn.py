#! /usr/bin/env python3
# -*- coding=utf-8

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging
import os.path as path
import pymongo
import urllib.parse
import bgmi.config
import os
from bgmi.front.index import get_player
from bgmi.lib.models import Followed
from bgmi.utils import normalize_path
import pathlib
import json
import datetime
import pytz

base_dir = pathlib.Path(path.dirname(__file__))
log_file = str(path.abspath(base_dir / 'bgmi.log'))

logging.basicConfig(level=logging.DEBUG, filename=log_file)
root = logging.getLogger()

root.setLevel(logging.DEBUG)
root.addHandler(logging.FileHandler(log_file, encoding='utf-8', mode='a+', ))
root.addHandler(logging.StreamHandler(sys.stdout))

# logging = logging.getLogger()
line = json.dumps(sys.argv)
logging.info(line)

logging.info('start: {}'.format(datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))))
l = Followed.select().dicts()
save_path = bgmi.config.SAVE_PATH
url_encode = urllib.parse.quote

secret_id = 'AKIDQlwc7RHZN6e1GKmvdDcqskUFyY8ne6oS'  # 替换为用户的 secretId
secret_key = 'fEoQtDPQL5e2OWWM2f9SaXLyXyKanpgM'  # 替换为用户的 secretKey
region = 'ap-shanghai'  # 替换为用户的 Region
Bucket = 'bgmi-1-1251776811'
scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

config = CosConfig(Region=region,
                   SecretId=secret_id,
                   SecretKey=secret_key,
                   # Token=token,
                   Scheme=scheme)

client = CosS3Client(config)

file_path = r'C:\Users\Niu\.bgmi\bangumi\海贼王\1\DeepMind open source PySC2 toolset for Starcraft II.mp4'
if len(sys.argv) >= 2:
    file_path = sys.argv[-1]

filename = path.basename(file_path)
if not (file_path.endswith('.mp4') or file_path.endswith('.mkv')):
    exit(1)

dir_name = path.dirname(file_path).replace(save_path + os.sep, '')

logging.info(filename)
logging.info(dir_name)
episode = None
bangumi = None
try:

    for bgm in l:
        bangumi_name = normalize_path(bgm['bangumi_name'])
        if bangumi_name + os.sep in dir_name:
            logging.info(dir_name)
            episode = dir_name.replace(bangumi_name + os.sep, '')
            bangumi = bgm
            break

    g = get_player(bangumi['bangumi_name'])
    mp4_file = g[int(episode)]
    file_path = path.join(save_path, mp4_file['path'][1:] if mp4_file['path'].startswith('/') else mp4_file['path'])
    filename = path.basename(file_path)

    if bangumi:
        logging.info(filename)
        logging.info(file_path)
        logging.info(episode)
        logging.info(bangumi_name)
        logging.info('start uploading')
        response = client.upload_file(
            Bucket=Bucket,
            Key=filename,
            LocalFilePath=file_path,
            ContentType='video/mp4',
        )
        logging.info('finish uploading')
        mongoClient = pymongo.MongoClient()
        mongodb = mongoClient.get_database('bgmi')
        mongo_collection = mongodb.get_collection('bangumi')
        mongo_collection.update_one({'_id': bangumi['bangumi_name']},
                                    {'$set': {
                                        'player.{}'.format(episode): {'path': 'https://bgmi-1-1251776811.file.myqcloud.com/{}'.format(url_encode(filename))}
                                    }},
                                    upsert=True)
        logging.debug(mongo_collection.find_one({'_id': bangumi['bangumi_name']}))
    else:
        logging.warning('no bangumi')
        logging.info(filename)
        logging.info(file_path)
        logging.info(episode)
except Exception as e:
    logging.error(e)
logging.info('')
logging.info('end: {}'.format(datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))))
