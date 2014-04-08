# -*- coding: utf-8 -*-
import Image, ImageFile
from StringIO import StringIO

def resize(data, mimetype, width=None, height=None, ratio=None):
    if height is None and width is None and ratio is None:
        return data
    format = mimetype.split('/')[1].split(';')[0]
    image = Image.open(StringIO(data))
    if width is None:
        width = image.size[0]
    width = int(width)
    if height is None:
        height = image.size[1]
    height = int(height)
    if ratio is None:
        if height and height != image.size[1]:
            ratio = float(height)/image.size[1]
        elif width and width != image.size[0]:
            ratio = float(width)/image.size[0]
        else:
            ratio = 1
    try:
        ratio = float(ratio)
    except TypeError:
        print(ratio)
    height = int(image.size[1]*ratio)
    width = int(image.size[0]*ratio)
    size = (width, height)
    if image.size != size:
        filter = Image.BICUBIC
        if image.size[0] > size[0] and image.size[1] > size[1]:
            filter = Image.ANTIALIAS
        image = image.resize(size, filter)
        output = StringIO()
        if format.lower() == 'jpeg':
            try:
                image.save(output, "JPEG", quality=50, optimize=True, progressive=True)
            except IOError:
                ImageFile.MAXBLOCK = image.size[0] * image.size[1]
                image.save(output, "JPEG", quality=50, optimize=True, progressive=True)
        else:
            image.save(output, format)
        data = output.getvalue()
    return data
