import logging
import json
import os

import requests


class YaDiskUploader:
    url = 'https://cloud-api.yandex.net/v1/disk/'

    module_logger = logging.getLogger('YaDiskUploader')

    def __init__(self, token):
        self.token = token

    def _get_headers(self):
        return {
            'Content-type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def create_folder(self, path):
        """
        Создает директорию path на Я.Диске
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'create_folder'))
        url_create = self.url + 'resources'
        params = {'path': path}
        response = requests.put(url=url_create, headers=self._get_headers(), params=params)
        # if response.status_code == 201:
        #     logger.info(f'Folder {path} is created')
        # elif response.status_code == 409:
        #     logger.info(f'Folder "{path}" existent directory')
        # return response.status_code
        if response.status_code == 409 and response.json()['error'] == 'DiskPathDoesntExistsError':
            temp = ''
            for i in [j for j in path.split('/')]:
                temp = f'{temp}/{i}'
                self.create_folder(temp)
        return response.status_code

    # def create_folders(self, path: str):
    #     """
    #     создает ветку директорий
    #     """
    #     url_create = self.url + 'resources'
    #     params = {'path': ''}
    #     response = str
    #     for i in path.split('/'):
    #         params['path'] += '/' + i
    #         response = requests.put(url=url_create, headers=self._get_headers(), params=params)
    #     return response.status_code

    def upload_photo(self, local_path_photo, path_disk, file_name):
        """
        Загружает файл на Диск
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'upload_photo'))

        full_path = f'{path_disk}/{file_name}'
        upload_url = self.get_upload_url(full_path)
        if upload_url.status_code == 200 and 'href' in upload_url.json():
            with open(local_path_photo, 'rb') as f:
                response = requests.put(url=upload_url.json()['href'], data=f)
            logger.info(f'{file_name} is uploaded')
            return True
        # elif upload_url.status_code == 409 and upload_url.json()['error'] == 'DiskPathDoesntExistsError':
        #     create = self.create_folders(path_disk)
        #     if create == 201:
        #         self.upload_photo(local_path_photo, path_disk, file_name)
        else:
            logger.error(f'{upload_url.json()}')
            return False

    def get_upload_url(self, path):
        """
        Получает ссылку для загрузки файла
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'get_upload_url'))
        upload_url = self.url + 'resources/upload'
        params = {'path': path, 'overwrite': 'true'}

        response = requests.get(upload_url, headers=self._get_headers(), params=params)

        return response

    def upload_photo_from_url(self, url, path_disk, file_name):
        """
        Загружает файл по url и загружает его на Диск
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'upload_photo_from_url'))
        response = requests.get(url)
        if response.status_code == 200:
            logger.info(f'Upload "{file_name}" is started')
            with open('temp.jpg', 'wb') as f:
                f.write(response.content)

            self.upload_photo('temp.jpg', path_disk, file_name)
            os.remove('temp.jpg')
            return True
        else:
            logger.error('Photo upload error')
            return False

    def upload_files_tree(self, files_tree, catalog_name=''):
        """
        Загружает папки с файлами на Диск
        """
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'upload_files_tree'))
        logger.info(f'Yandex Uploader is started')
        result = []

        if catalog_name:
            self.create_folder(catalog_name)

        for folder in files_tree:
            cur_folder = {'folder': folder['folder']}
            items_list = []
            logger.info(f'Upload folder "{folder["folder"]}" is started')

            folder_path = f'{catalog_name}/{folder["folder"]}'
            response = self.create_folder(folder_path)
            if response == 201 or response == 409:
                for item in folder['items']:
                    is_uploaded = self.upload_photo_from_url(
                        url=item['url'],
                        path_disk=folder_path,
                        file_name=item['name']
                    )
                    if is_uploaded:
                        items_list.append({'name': item['name'], 'size': item['size']})
            logger.info(f'Upload {folder["folder"]} was finished')
            cur_folder['items'] = items_list
            result.append(cur_folder)
        logger.info(f'Upload is finished')
        with open('result.json', 'w', encoding='utf8') as f:
            json.dump(result, f, ensure_ascii=False)
