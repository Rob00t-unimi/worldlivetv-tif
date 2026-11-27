# -*- coding: utf-8 -*-

class Plugin:
    def __init__(self, base_url=""):
        self.handle = 1

    def route(self, pattern):
        def decorator(func):
            return func
        return decorator

    def url_for(self, func, *args, **kwargs):
        return ""

    def run(self):
        pass
