#!/usr/bin/env python

import os
import re
import tempfile

from hashlib import md5
from simplejson import loads
from urllib import urlretrieve

from image_magick import resize

"""
settings should have the following attributes:

debug = {bool}

# flickr
flickr_api_key = {string}
flickr_user_id = {string}

# s3
aws_key = {string}
aws_secret = {string}
aws_bucket = {string}
s3_folder = {string}
"""
import settings

try:
    debug = settings.debug
except AttributeError:
    debug = False

flickr_suffixes = ('_m', '_n', '', '_z', '_c', '_b', '_o')
flickr_suffixes_widths = {
    '_m': 240,
    '_n': 320,
    '': 500,
    '_z': 640,
    '_c': 800,
    '_b': 1024,
    '_o': None
}
s3_folder = settings.s3_folder
# 31536000 => one year (which should be enough for anybody)
s3_headers =  { 'Cache-Control': 'max-age=31536000' }

"""
Extracts JSON from a JSONP result.
"""
def parse_jsonp(jsonp):
    return loads(jsonp[ jsonp.index("(") + 1 : jsonp.rindex(")") ])

"""
Builds a list of photo ID's from a Flickr API response.
"""
def extract_flickr_ids(flickr_photos):
    ids = []
    for photo in flickr_photos:
        ids.append(photo['id'])
    return ids

"""
Buids a dictionary of Flickr API data keyed by ID.
"""
def build_flickr_dict(flickr_photos):
    result = {}
    for photo in flickr_photos:
        result[photo['id']] = photo
    return result

"""
Gets all the photos from a Flickr stream.

Handles paging and gets the original file URL.
Expects a Flickr API object as a param.
"""
def get_flickr_photos(flickr):
    photos = []
    total_photos = 0

    def photo_page(page=1):
        return loads(flickr.photos_search(
            user_id=settings.flickr_user_id,
            page=page,
            per_page='100',
            format='json',
            extras='url_o'
        ))

    flickr_photos = photo_page()

    total_photos = int(flickr_photos['photos']['total'])

    photos.extend(flickr_photos['photos']['photo'])

    current_page = 2
    while total_photos > len(photos):
        photos.extend(photo_page(current_page)['photos']['photo'])
        current_page += 1

    return photos

"""
Gets the image filename out of a path.
"""
def extract_filename(name):
    matches = re.search(r'\/(.*\.(png|jpeg|jpg))$', name)
    if matches is not None:
        return matches.group(1)

"""
Lists all the image files in an S3 bucket.
"""
def get_s3_images(bucket):
    images = []
    for key in bucket.list(s3_folder):
        filename = extract_filename(key.name)
        if filename is not None:
            images.append(filename)
    return images

"""
Generate the filename to use for the S3 upload.
"""
def generate_s3_filename(base_filename, suffix, extension):
    return '%s%s.%s' % (base_filename, suffix, extension)

"""
Uploads a file to S3.

Does not upload if debug is True.
"""
def send_to_s3(key, filename, s3_name):
    if debug:
        print('Would have uploaded file to S3: %s' % (s3_name))
        return
    else:
        print('Uploading file to S3: %s' % (s3_name))
        key.set_contents_from_filename(filename, headers=s3_headers, reduced_redundancy=True)
        key.make_public()

"""
Extracts the extension from a filename.
"""
def get_file_extension(filename):
    matches = re.search(r'.*\.(.*?)$', filename)
    return matches.group(1).lower()

"""
Helper function to get the new extension based on the suffix and extension.
"""
def new_extension(suffix, extension):
    if suffix == '_o' and extension == 'png':
        return 'png'
    else:
        return 'jpeg'

"""
Downlads a flickr URL to a temp directory.
"""
def download_flickr_to_temp(flickr_url, temp_dir):
    download = True
    file_name = '%s/%s.%s' % (temp_dir, md5(flickr_url).hexdigest(), get_file_extension(flickr_url))
    mode = 'w+b'
    if os.path.exists(file_name):
        mode = 'rb'
        download = False
    temp_file = open(file_name, mode)
    if download:
        urlretrieve(flickr_url, temp_file.name)
    return temp_file

"""
Helper function to handle the call to the resize function.
"""
def resize_image(image_data, suffix, output_file):
    resize(
        image_data.name,
        flickr_suffixes_widths[suffix],
        output_file,
        get_file_extension(output_file),
    )



def main():

    # Flickr setup.
    import flickrapi
    flickr = flickrapi.FlickrAPI(settings.flickr_api_key, settings.flickr_secret, cache=False)
    photos = get_flickr_photos(flickr)
    flickr_images = build_flickr_dict(photos)

    # S3 setup.
    from boto.s3.connection import S3Connection
    from boto.s3.key import Key
    conn = S3Connection(settings.aws_key, settings.aws_secret)
    bucket = conn.get_bucket(settings.aws_bucket)
    s3_files = get_s3_images(bucket)

    # Named tempdir for debugging to save re-downloading from Flickr each time.
    temp_dir = None
    if debug:
        temp_dir = '/tmp/flickr2s3_test'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    upload_count = 0

    for flickr_id in flickr_images:
        original_url = flickr_images[flickr_id]['url_o']
        extension = get_file_extension(original_url)

        suffixes = []
        for suffix in flickr_suffixes:
            if not generate_s3_filename(
                flickr_id,
                suffix,
                new_extension(suffix, extension)
            ) in s3_files:
                suffixes.append(suffix)

        if len(suffixes):
            if temp_dir is None:
                temp_dir = tempfile.mkdtemp(prefix='flickr2s3')
            temp_file = download_flickr_to_temp(original_url, temp_dir)
            for suffix in suffixes:
                s3_name = generate_s3_filename(
                    flickr_id,
                    suffix,
                    new_extension(suffix, extension)
                )

                k = Key(bucket, '%s/%s' % (s3_folder, s3_name))
                tempfilename = '%s/%s' % (temp_dir, s3_name)

                resize_image(temp_file, suffix, tempfilename)
                send_to_s3(k, tempfilename, s3_name)
                upload_count += 1

            temp_file.close()
            #delete flickr temp file
    #delete temp dir

    if upload_count == 0:
        print('No files found to upload.')

if __name__ == '__main__':
    import logging
    logging.captureWarnings(True)
    main()
