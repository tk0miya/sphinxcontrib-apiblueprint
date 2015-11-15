# -*- coding: utf-8 -*-
import re
from docutils import nodes


class ParseError(Exception):
    pass


class Section(nodes.Element):
    pass


class ResourceGroup(Section):
    pass


class Resource(Section):
    def parse_title(self):
        from sphinxcontrib.apiblueprint.utils import extract_option
        self['uri'] = ''
        self['http_method'] = ''
        self['identifier'] = ''

        title = self[0].astext()
        parts = title.split()
        option = extract_option(title)
        if len(parts) == 1:
            # <URI template>
            self['uri'] = parts[0]
        elif len(parts) == 2 and option is None:
            # <HTTP request method> <URI template>
            self['http_method'] = parts[0]
            self['uri'] = parts[1]
        else:
            options = option.split()
            if len(options) == 1:
                # <identifier> [<URI template>]
                self['identifier'] = parts[0]
                self['uri'] = options[0]
            else:
                # <identifier> [<HTTP request method> <URI template>]
                self['identifier'] = re.sub('\s*\[(.*)\]$', '', title)
                self['http_method'] = options[0]
                self['uri'] = options[1]


class Model(Section):
    pass


class Schema(Section):
    pass


class Action(Section):
    pass


class Request(Section):
    pass


class Response(Section):
    def parse_title(self):
        matched = re.search('^Response\s+(\d+)\s+\((.+)\)$', self[0].astext())
        if not matched:
            raise ParseError('Unknown response type: %s' % self[0].astext())

        self['status_code'] = int(matched.group(1))
        self['content_type'] = matched.group(2).strip()


class Parameters(Section):
    pass


class Attributes(Section):
    pass


class Headers(Section):
    pass


class Body(Section):
    pass


class DataStructures(Section):
    pass


class Relation(Section):
    pass
