from subprocess import call
import imghdr

"""
Uses imagemagick as an external call to resize a file and save as progressive.
"""
def resize(input_file, size, output_file, img_type):
    if (size is not None) :
        input_file = '%s[%sx%s]' % (input_file, size, size)
    if img_type in ('jpg', 'jpeg'):
        interlace = 'JPEG'
        quality = '75' # Higher -> less dropped bits
    elif img_type == 'png':
        interlace = 'PNG'
        # http://www.imagemagick.org/Usage/formats/#png_quality
        quality = '90' # Higher -> more compression (Only adjust in multiples of 10?)
    call([
        'convert',
        '-strip',
        '-interlace', interlace,
        '-quality', quality,
        input_file,
        output_file,
    ], shell=False)

