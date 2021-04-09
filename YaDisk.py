import logging
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
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'create_folder'))
        url_create = self.url + 'resources'
        params = {'path': path}
        response = requests.put(url=url_create, headers=self._get_headers(), params=params)
        if response.status_code == 201:
            logger.info(f'Folder {path} is created')
        elif response.status_code == 409:
            logger.info(f'Folder "{path}" existent directory')
        return response.status_code

    def create_folders(self, path: str):
        url_create = self.url + 'resources'
        params = {'path': ''}
        response = str
        for i in path.split('/'):
            params['path'] += '/' + i
            response = requests.put(url=url_create, headers=self._get_headers(), params=params)
        return response.status_code

    def upload_photo(self, local_path_photo, path_disk, file_name):

        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'upload_photo'))

        full_path = f'{path_disk}/{file_name}'
        upload_url = self.get_upload_url(full_path)

        if upload_url.status_code == 200:
            with open(local_path_photo, 'rb') as f:
                response = requests.put(url=upload_url.json()['href'], data=f)
            logger.info(f'{file_name} is uploaded')
        elif upload_url.status_code == 409 and upload_url.json()['error'] == 'DiskPathDoesntExistsError':
            create = self.create_folders(path_disk)
            if create == 201:
                self.upload_photo(local_path_photo, path_disk, file_name)
        else:
            logger.error(f'{upload_url.json()}')

    def get_upload_url(self, path):
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'get_upload_url'))
        upload_url = self.url + 'resources/upload'
        params = {'path': path, 'overwrite': 'true'}

        response = requests.get(upload_url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            logger.info(f'url for {path} was received')
        else:
            logger.info(f'{response.json()}')
        return response

    def upload_photo_from_url(self, url, path_disk, file_name):
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'upload_photo_from_url'))
        response = requests.get(url)
        if response.status_code == 200:
            logger.info(f'Upload {file_name} is started')
            with open('temp.jpg', 'wb') as f:
                f.write(response.content)

            self.upload_photo('temp.jpg', path_disk, file_name)
            os.remove('temp.jpg')
        else:
            logger.info('Photo upload error')

    def upload_files_tree(self, files_tree, catalog_name=''):
        logger = logging.getLogger('{}.{}'.format(self.module_logger.name, 'upload_files_tree'))
        logger.info(f'Yandex Uploader is started')

        if catalog_name:
            response = self.create_folder(catalog_name)

        for folder in files_tree:

            logger.info(f'Upload {folder["folder"]} is started')

            folder_path = f'{catalog_name}/{folder["folder"]}'
            response = self.create_folder(folder_path)
            if response == 201 or response == 409:
                for item in folder['items']:

                    self.upload_photo_from_url(
                        url=item['url'],
                        path_disk=folder_path,
                        file_name=item['name']
                    )
            logger.info(f'Upload {folder["folder"]} is done')
        logger.info(f'Upload is done')







