import xbmc

class MyLogger():

    def __init__(self, level: int) -> None:
        self.level = level

    def error(self, s):

        self.log(s)

    def warning(self, s):

        self.log(s)

    def info(self, s):

        self.log(s)

    def debug(self, s):

        self.log(s)

    def log(self, s):

        xbmc.log(s, self.level)