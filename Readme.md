# Flickr to S3

Copes images in a Flickr stream to S3 and converts them to progressive/ interlaced format.

## Python modules
Requires:

 * boto (for S3)
 * flickrapi (for Flickr)

## Command line utilities
Requires:

 * convert (ImageMagick)

## Setup
You need to create a settings module that has the following attributes:

 * debug = {bool}
 * flickr_api_key = {string}
 * flickr_user_id = {string}
 * aws_key = {string}
 * aws_secret = {string}
 * aws_bucket = {string} # Bucket name (must exist)
 * s3_folder = {string} # Folder name within bucket (must exist)

## Usage
Run `flickr2s3.py` from the command line.

## Tests
Run `python -m unittest tests` from the command line.
