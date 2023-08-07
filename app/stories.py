class Story:
    def __init__(self, storyteller, image, info):
        self._storyteller = storyteller
        self._image = image
        self._info = info
        self._likes = 0
        self._comments = []

    def get_storyteller(self):
        return self._storyteller

    def get_image(self):
        return self._image

    def get_info(self):
        return self._info

    def get_likes(self):
        return self._likes

    def get_comments(self):
        return self._comments

    def set_storyteller(self, storyteller):
        self._storyteller = storyteller

    def set_info(self, info):
        self._info = info

    def set_likes(self, likes):
        self._likes = likes

    def set_comments(self, comments):
        self._comments = comments

    def set_image(self, image):
        self._image = image
