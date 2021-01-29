#!/usr/bin/env python 
# -*- coding:utf-8 -*-
# @Time    : 2019-1-24 23:15
# @Author  : liujin_person

class Dict(dict):
    """
    创建字典类，self.key,self[key]均可调用value值
    """

    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value
