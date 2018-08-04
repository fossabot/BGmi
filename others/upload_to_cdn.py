#! /usr/bin/env python3
# -*- coding=utf-8
import time

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging
import os.path as path
import pymongo
import urllib.parse
import bgmi.config
import os
from bgmi.lib.models import Followed
from bgmi.utils import normalize_path
import pathlib
import json
import datetime
import pytz

from others.user_config import secret_id, secret_key, region, Bucket


def get_player(bangumi_name):
    episode_list = {}
    # new path

    if os.path.exists(os.path.join(bgmi.config.SAVE_PATH, normalize_path(bangumi_name))):
        bangumi_name = normalize_path(bangumi_name)
    bangumi_path = os.path.join(bgmi.config.SAVE_PATH, bangumi_name)
    path_walk = os.walk(bangumi_path)

    logger.debug('os.walk(bangumi_path) => {}'.format(bangumi_path))
    for root, _, files in path_walk:
        _ = root.replace(bangumi_path, '').split(os.path.sep)
        base_path = root.replace(bgmi.config.SAVE_PATH, '')
        if len(_) >= 2:
            episode_path = root.replace(os.path.join(bgmi.config.SAVE_PATH, bangumi_name), '')
            if episode_path.split(os.path.sep)[1].isdigit():
                episode = int(episode_path.split(os.path.sep)[1])
            else:
                continue
        else:
            episode = -1

        for bangumi in files:
            if any([bangumi.lower().endswith(x) for x in ['.mp4', '.mkv']]):
                video_file_path = os.path.join(base_path, bangumi)
                video_file_path = os.path.join(os.path.dirname(video_file_path), os.path.basename(video_file_path))
                video_file_path = video_file_path.replace(os.path.sep, '/')
                episode_list[episode] = {'path': video_file_path}
                break

    return episode_list


base_dir = pathlib.Path(path.dirname(__file__))
log_file = str(path.abspath(base_dir / 'bgmi.log'))

logging.basicConfig(level=logging.INFO, filename=log_file)

logging.getLogger('qcloud_cos.cos_client').setLevel(logging.INFO)
logging.getLogger('BGmi').setLevel(logging.WARNING)

logger = logging.getLogger('on_bt_finish')

logger.setLevel(logging.DEBUG)
logger.addHandler(logging.FileHandler(log_file, encoding='utf-8', mode='a+', ))
logger.addHandler(logging.StreamHandler(sys.stdout))

# logger = logger.getLogger()
line = json.dumps(sys.argv)
logger.info(line)

logger.info('start: {}'.format(datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))))
l = Followed.select().dicts()
save_path = bgmi.config.SAVE_PATH
url_encode = urllib.parse.quote


file_path = r'C:\Users\Niu\.bgmi\bangumi\海贼王\1\DeepMind open source PySC2 toolset for Starcraft II.mp4'
if len(sys.argv) >= 2:
    file_path = sys.argv[-1]

filename = path.basename(file_path)
if not (file_path.endswith('.mp4') or file_path.endswith('.mkv')):
    exit(1)

dir_name = path.dirname(file_path).replace(save_path + os.sep, '')

logger.info(filename)
logger.info(dir_name)
episode = None
bangumi = None
try:

    for bgm in l:
        bangumi_name = normalize_path(bgm['bangumi_name'])
        if bangumi_name + os.sep in dir_name:
            logger.info(dir_name)
            episode = dir_name.replace(bangumi_name + os.sep, '')
            bangumi = bgm
            break

    g = get_player(bangumi['bangumi_name'])
    print(g)
    mp4_file = g[int(episode)]
    file_path = path.join(save_path, mp4_file['path'][1:] if mp4_file['path'].startswith('/') else mp4_file['path'])
    filename = path.basename(file_path)
    logger.info(filename)
    logger.info(file_path)
    logger.info(episode)
    if bangumi:
        logger.info(bangumi_name)
        logger.info('start uploading')

        scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

        config = CosConfig(Region=region,
                           SecretId=secret_id,
                           SecretKey=secret_key,
                           # Token=token,
                           Scheme=scheme)

        client = CosS3Client(config)
        response = client.upload_file(
            Bucket=Bucket,
            Key=filename,
            LocalFilePath=file_path,
            ContentType='video/mp4',
        )

        logger.info('finish uploading')
        mongoClient = pymongo.MongoClient()
        mongodb = mongoClient.get_database('bgmi')
        mongo_collection = mongodb.get_collection('bangumi')
        mongo_collection.update_one({'_id': bangumi['bangumi_name']},
                                    {'$set': {
                                        'player.{}'.format(episode): 'https://bgmi-1-1251776811.file.myqcloud.com/{}'.format(url_encode(filename)),
                                        "updated_time": int(time.time()),
                                        "episode": int(episode),
                                    }},
                                    upsert=True)
        logger.debug(mongo_collection.find_one({'_id': bangumi['bangumi_name']}))
    else:
        logger.warning('no bangumi')
        logger.info(filename)
        logger.info(file_path)
        logger.info(episode)
except Exception as e:
    logger.error(str(e))
    raise e
logger.info('')
logger.info('end: {}'.format(datetime.datetime.now(tz=pytz.timezone('Asia/Shanghai'))))
