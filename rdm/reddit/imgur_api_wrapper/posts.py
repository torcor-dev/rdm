class ImgurModel:
    def __init__(self, *args, **kwargs):
        for arg in args:
            for k, v in arg.items():
                if isinstance(v, dict):
                    for ik, iv in v.items():
                        setattr(self, ik, iv)
                setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)


class Image(ImgurModel):
    def __init__(self, *args, **kwargs):
        self.type = "image"
        super().__init__(*args, **kwargs)


class Album(ImgurModel):
    def __init__(self, *args, **kwargs):
        self.type = "album"
        self.images = []
        super().__init__(*args, **kwargs)
        self.images = [Image(img) for img in self.images]


class Gallery(ImgurModel):
    def __init__(self, *args, **kwargs):
        self.type = "gallery"
        self.images = []
        super().__init__(*args, **kwargs)
        self.images = [Image(img) for img in self.images]
