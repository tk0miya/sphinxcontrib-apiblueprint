# -*- coding: utf-8 -*-
import re
from docutils import nodes


class ParseError(Exception):
    pass


class Section(nodes.Element):
    pass


class ResourceGroup(Section):
    def parse_title(self):
        _, identifier = self[0].astext().split(None, 1)
        self['identifier'] = identifier


class Resource(Section):
    def parse_title(self):
        from sphinxcontrib.apiblueprint.utils import extract_option
        self['uri'] = ''
        self['http_method'] = ''
        self['identifier'] = ''
        self['has_action'] = False

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
                self['identifier'] = re.sub('\s*\[(.*)\]$', '', title)
                self['uri'] = options[0]
            else:
                # <identifier> [<HTTP request method> <URI template>]
                self['identifier'] = re.sub('\s*\[(.*)\]$', '', title)
                self['http_method'] = options[0]
                self['uri'] = options[1]

    def restruct(self):
        from sphinxcontrib.apiblueprint.utils import get_children

        actions = get_children(self, Action)
        if actions:
            self['has_action'] = True
            for subnode in actions:
                if self['uri'] and subnode.get('uri') is None:
                    subnode['uri'] = self['uri']


class Model(Section):
    pass


class Schema(Section):
    pass


class Action(Section):
    def parse_title(self):
        matched = re.search('^(.*)\s+\[(.*)\]$', self[0].astext())
        self['identifier'] = matched.group(1)
        self['http_method'] = matched.group(2)


class Request(Section):
    pass


class Response(Section):
    def parse_title(self):
        matched = re.search('^Response\s+(\d+)(?:\s+\((.+)\))?$', self[0].astext())
        if not matched:
            raise ParseError('Unknown response type: %s' % self[0].astext())

        self['status_code'] = int(matched.group(1))
        self['content_type'] = (matched.group(2) or '').strip()

    def restruct(self):
        from sphinxcontrib.apiblueprint.utils import get_children, transpose_subnodes

        if not get_children(self, Section):
            body = Body()
            transpose_subnodes(self, body)
            self += body
            body.dedent()

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
            literal.replace_self(nodes.literal_block(text=new_header))


class Body(Section):
    def dedent(self):
        from textwrap import dedent
        from sphinxcontrib.apiblueprint.utils import get_children

        for subnode in get_children(self, (nodes.literal_block, nodes.paragraph)):
            content = dedent(subnode.astext())
            subnode.replace_self(nodes.literal_block(text=content))


class DataStructures(Section):
    pass


class Relation(Section):
    pass
