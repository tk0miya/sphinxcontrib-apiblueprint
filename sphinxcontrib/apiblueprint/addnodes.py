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

    def restruct(self):
        from sphinxcontrib.apiblueprint.utils import get_children, transpose_subnodes

        if not get_children(self, Section):
            body = Body()
            transpose_subnodes(self, body)
            self += body

        headers = get_children(self, Headers)
        if not headers:
            header = Headers()
            header.add_header('Content-Type: %s' % self['content_type'])

            body = get_children(self, Body)[0]
            pos = self.index(body)
            self.insert(pos, header)
        else:
            for header in headers:
                header.add_header('Content-Type: %s' % self['content_type'])


class Parameters(Section):
    pass


class Attributes(Section):
    pass


class Headers(Section):
    def add_header(self, header):
        from sphinxcontrib.apiblueprint.utils import get_children

        if len(self) == 0:
            self += nodes.literal_block(text=header)
        else:
            literal = get_children(self, nodes.literal_block)[0]
            new_header = header + "\n" + literal.astext()
            literal[0].replace_self(nodes.Text(new_header))


class Body(Section):
    pass


class DataStructures(Section):
    pass


class Relation(Section):
    pass
