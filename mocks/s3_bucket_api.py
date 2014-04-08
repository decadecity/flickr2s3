
class KeyMock:

    def __init__(self, name):
        self.name = name



class BucketMock:

    def list(self, *args):
        keys = ['images/', 'images/8286137174.jpeg', 'images/8286137175.jpeg', 'images/8286137176.jpeg']
        result = []
        for key in keys:
            result.append(KeyMock(key))
        return result


bucket = BucketMock()
