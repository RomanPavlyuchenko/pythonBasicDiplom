import json
import logging

import VK
import YaDisk

# vk_token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'

if __name__ == '__main__':
    with open('tokens.json') as tokens:
        data = json.load(tokens)
        vk_token = data['vk_token']
        ya_token = data['ya_token']

    vk_user = VK.VKUser(vk_token, '5.130')
    ya_uploader = YaDisk.YaDiskUploader(ya_token)

    file_log = logging.FileHandler('Log.log', 'w')
    file_log.setLevel(logging.ERROR)
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=(file_log, console_out),
                        format='[%(asctime)s | %(name)s | %(levelname)s]: %(message)s',
                        datefmt='%m.%d.%Y %H:%M:%S',
                        level=logging.INFO)
    logger = logging.getLogger('backuper')

    photos = vk_user.get_all_photos()
    ya_uploader.upload_files_tree(photos)
