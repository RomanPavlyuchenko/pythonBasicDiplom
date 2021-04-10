import logging
from datetime import datetime
from time import sleep

import requests


def _get_likes_name(data):
    """
    Назначает имена фотографиям в альбоме согласно количеству лайков на них.
    При совпадении у двух фото количества лайков, добавляет к ним дату и время загрузки
    """
    photos_tree = []

    for album in data:
        cur_album = {'folder': album['folder']}
        likes = [i['likes'] for i in album['items']]
        cur_album['items'] = []
        for item in album['items']:
            if likes.count(item['likes']) == 1:
                cur_album['items'].append({'name': str(item['likes']), 'url': item['url'], 'size': item['size']})
            else:
                date_time = datetime.utcfromtimestamp(item['date']).strftime(' %d-%m-%Y %H.%M.%S')
                cur_album['items'].append(
                    {'name': '{} {}'.format(item['likes'], date_time),
                     'url': item['url'],
                     'size': item['size']}
                )
        photos_tree.append(cur_album)

    return photos_tree


def _best_photos(data):
    """
    Выбирает с списка фотографий, фото с лучшим качеством
    """
    photos_list = []
    for item in data:
        max_size = 0
        max_url = ''
        last_url = ''
        size = ''

        for i in item['sizes']:
            curr_max = i['height'] * i['width']

            if curr_max > max_size:
                max_size = curr_max
                max_url = i['url']
                size = i['type']
            last_url = i['url']
            last_size = i['type']
        if not max_url:
            max_url = last_url
            size = last_size
        inform = {'url': max_url, 'date': item['date'], 'likes': item['likes']['count'], 'size': size}

        photos_list.append(inform)
    return photos_list


class VKUser:
    url = 'https://api.vk.com/method/'
    module_logger = logging.getLogger('VK')

    def __init__(self, token, version):
        self.token = token
        self.version = version
        self.params = {
            'access_token': self.token,
            'v': self.version
        }
        self.owner_id = requests.get(self.url + 'users.get', self.params).json()['response'][0]['id']

    def get_photos(self, owner_id=None, count=5, album_id='profile', extended=1):
        """
        Возвращает список фото из альбома album_id(по умолчанию аватарки пользователя) пользователя
        owner_id(по умолчанию владельца токена) в количестве count.
        Если count == 0, то запрашивает все фото.
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'get_photos'))
        if owner_id is None:
            owner_id = self.owner_id
        photos_url = self.url + 'photos.get'
        photos_params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'extended': extended
        }
        if count == 0 or count > 1000:
            photos_params['count'] = 1000
        else:
            photos_params['count'] = count

        photos_list = []

        response = requests.get(photos_url, params={**self.params, **photos_params})
        if response.status_code != 200 or 'error' in response.json():
            logger.error(f'{response.json()}')
            return []
        items = response.json()['response']['items']
        if count == 0:
            offset = 0
            while items:
                photos_list.extend(_best_photos(items))

                offset += 1000
                sleep(0.5)

                response = requests.get(photos_url, params={**self.params, **photos_params, **{'offset': offset}})
                if response.status_code != 200 or 'error' in response.json():
                    logger.error(f'{response.json()}')
                    return []
                items = response.json()['response']['items']

        else:
            offset = 0
            while items:
                photos_list.extend(_best_photos(items))
                if count <= 1000:
                    break

                offset += 1000
                sleep(0.5)

                if count != 0:
                    photos_params['count'] = count - 1000
                    count -= 1000

                response = requests.get(photos_url, params={**self.params, **photos_params, **{'offset': offset}})
                if response.status_code != 200 or 'error' in response.json():
                    logger.error(f'{response.json()}')
                    return []
                items = response.json()['response']['items']

        logger.info(f'Photos from {album_id} was received')

        return photos_list

    def get_albums_list(self, owner_id=None):
        """
        Возвращает список всех альбомов пользователя
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'get_albums_list'))
        if owner_id is None:
            owner_id = self.owner_id
        album_url = self.url + 'photos.getAlbums'
        album_params = {
            'owner_id': owner_id
        }
        response = requests.get(album_url, params={**self.params, **album_params})
        if response.status_code != 200 or 'error' in response.json():
            logger.error(f'{response.json()}')
            return []

        album_list = []
        for item in response.json()['response']['items']:
            album_list.append({'album_id': item['id'], 'title': item['title']})

        logger.info('album_list was received')
        return album_list

    def get_all_photos(self, owner_id=None, count=0):
        """
        возвращает список всех альбомов пользователя, со всеми фото.
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'get_all_photos'))
        logger.info('Started')
        all_photos = []
        photos = self.get_photos(count=count, owner_id=owner_id)
        all_photos.append({'folder': 'profile', 'items': photos})
        album = self.get_albums_list(owner_id)

        for item in album:
            photos = self.get_photos(count=count, album_id=item['album_id'])
            all_photos.append({
                'folder': item['title'],
                'items': photos})
            sleep(1.5)
        tree = _get_likes_name(all_photos)
        logger.info('Done')

        return tree
