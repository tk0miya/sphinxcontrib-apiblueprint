# -*- coding: utf-8 -*-
import re
from docutils import nodes
from textwrap import dedent
from sphinxcontrib.apiblueprint.utils import (
    HTTP_METHODS, extract_option, get_children, transpose_subnodes
)


class ParseError(Exception):
    pass


class Section(nodes.Element):
    @classmethod
    def parse_node(cls, node):

        section = cls(**node.attributes)
        transpose_subnodes(node, section)
        section.parse_title()
        section.parse_content()
        return section

    def parse_title(self):
        self.pop(0)

    def parse_content(self):
        pass


class PayloadSection(Section):
    """
    An abstract class for Payload section
    https://apiblueprint.org/documentation/specification.html#def-payload-section

    The section inherits this class can have some nested sections:
    * 0 or 1 Headers Section
    * 0 or 1 Attributes Section
    * 0 or 1 Body Section
    * 0 or 1 Schema Section

    If there is no nested sections, the content is considered as Body section.
    """

    def parse_content(self):
        """restructs nested sections:

        * consider the contents as Body section if no nested sections
        * merge content-type to Header section
        """
        if len(self) > 0 and not get_children(self, Section):
            body = Body()
            transpose_subnodes(self, body)
            self += body
            body.dedent()

        if self.get('content_type'):
            headers = get_children(self, Headers)
            if not headers:
                header = Headers()
                header.add_header('Content-Type: %s' % self['content_type'])

                bodies = get_children(self, Body)
                if len(bodies) == 0:
                    self.append(header)
                else:
                    pos = self.index(bodies[0])
                    self.insert(pos, header)
            else:
                for header in headers:
                    header.add_header('Content-Type: %s' % self['content_type'])


class ResourceGroup(Section):
    def parse_title(self):
        _, identifier = self.pop(0).astext().split(None, 1)
        self['identifier'] = identifier


class Resource(Section):
    def parse_title(self):
        title = self.pop(0).astext()
        parts = title.split()
        option = extract_option(title)
        if len(parts) == 1:
            # <URI template>
            self['identifier'] = ''
            self['uri'] = parts[0]
        else:
            # <identifier> [<URI template>]
            self['identifier'] = re.sub('\s*\[(.*)\]$', '', title)
            self['uri'] = option

    def parse_content(self):
        for node in get_children(self, Action):
            if node.get('uri') is None:
                node['uri'] = self['uri']


class Model(Section):
    pass


class Schema(Section):
    pass


class Action(Section):
    def parse_title(self):
        title = self.pop(0).astext().strip()
        option = extract_option(title)
        if title in HTTP_METHODS:
            # <HTTP request method>
            self['identifier'] = ''
            self['http_method'] = title
            self['uri'] = None
        elif option is None:
            # <HTTP request method> <URI template>
            http_method, uri = title.split()
            self['identifier'] = ''
            self['http_method'] = http_method
            self['uri'] = uri
        else:
            matched = re.search('^(.*)\s+\[(.*)\]$', title)
            self['identifier'] = matched.group(1)
            parts = matched.group(2).split()
            if len(parts) == 1:
                # <identifier> [<HTTP request method>]
                self['http_method'] = parts[0]
                self['uri'] = None
            else:
                # <identifier> [<HTTP request method> <URI template>]
                self['http_method'] = parts[0]
                self['uri'] = parts[1]


class Request(PayloadSection):
    def parse_title(self):
        title = self.pop(0).astext()
        matched = re.search('^Request(?:\s+(.+))?$', title)
        if not matched:
            raise ParseError('Unknown response type: %s' % title)

        argument = matched.group(1) or ''
        matched = re.search('^(.*?\s+)?\((.+)\)$', argument)
        if matched:
            self['identifier'] = (matched.group(1) or '').strip()
            self['content_type'] = (matched.group(2) or '').strip()
        else:
            self['identifier'] = argument
            self['content_type'] = ''


class Response(PayloadSection):
    def parse_title(self):
        title = self.pop(0).astext()
        matched = re.search('^Response\s+(\d+)(?:\s+\((.+)\))?$', title)
        if not matched:
            raise ParseError('Unknown response type: %s' % title)

        self['status_code'] = int(matched.group(1))
        self['content_type'] = (matched.group(2) or '').strip()


class Parameters(Section):
    pass


class Attributes(Section):
    pass


class Headers(Section):
    def add_header(self, header):
        if len(self) == 0:
            self += nodes.literal_block(text=header)
        else:
            literal = get_children(self, (nodes.literal_block, nodes.paragraph))[0]
            new_header = header + "\n" + literal.astext()
            literal.replace_self(nodes.literal_block(text=new_header))


class Body(Section):
    def parse_content(self):
        self.dedent()

    def dedent(self):
        for subnode in get_children(self, (nodes.literal_block, nodes.paragraph)):
            content = dedent(subnode.astext())
            subnode.replace_self(nodes.literal_block(text=content))


class DataStructures(Section):
    pass


class Relation(Section):
    pass
