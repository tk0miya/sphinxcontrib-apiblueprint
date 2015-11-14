# -*- coding: utf-8 -*-


def transpose_subnodes(old, new):
    for subnode in old[:]:
        old.remove(subnode)
        new += subnode
