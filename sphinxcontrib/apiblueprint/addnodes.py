# -*- coding: utf-8 -*-
import re
from docutils import nodes
from textwrap import dedent
from sphinx import addnodes as sphinxnodes
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
        section.validate()
        section.parse_title()
        section.parse_content()
        return section

    def parse_title(self):
        self.pop(0)

    def parse_content(self):
        pass

    def validate(self):
        pass

    def assert_having_only(self, classes):
        if isinstance(classes, (list, tuple)):
            class_names = [cls.__name__ for cls in classes]
        else:
            class_names = [classes.__name__]

        nodes = get_children(self, Section)
        assert len(nodes) == 0 or all(isinstance(node, classes) for node in nodes), \
            "%s section should have only following sections: %s" % (self.__class__.__name__, class_names)

    def assert_having_no_sections(self):
        nodes = get_children(self, Section)
        assert len(nodes) == 0, \
            "%s section should not have any sections" % (self.__class__.__name__)

    def assert_having_at_most_one(self, cls):
        nodes = get_children(self, cls)
        assert len(nodes) <= 1, \
            "%s section should have at most one %s section" % (self.__class__.__name__, cls.__name__)

    def assert_having_any(self, cls):
        pass  # nothing to assert; only declaration

    def assert_having_at_least_one(self, cls):
        nodes = get_children(self, cls)
        assert len(nodes) >= 1, \
            "%s section should have at least one of %s sections" % (self.__class__.__name__, cls.__name__)


class AssetSection(Section):
    def parse_content(self):
        self.dedent()

    def dedent(self):
        for subnode in get_children(self, (nodes.literal_block, nodes.paragraph)):
            content = dedent(subnode.astext())
            subnode.replace_self(nodes.literal_block(text=content))

    def validate(self):
        self.assert_having_no_sections()


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
                header.headers.insert(0, 'Content-Type: %s' % self['content_type'])

                bodies = get_children(self, Body)
                if len(bodies) == 0:
                    self.append(header)
                else:
                    pos = self.index(bodies[0])
                    self.insert(pos, header)
            else:
                for header in headers:
                    header.headers.insert(0, 'Content-Type: %s' % self['content_type'])

    def validate(self):
        self.assert_having_only((Headers, Attributes, Body, Schema))
        self.assert_having_at_most_one(Headers)
        self.assert_having_at_most_one(Attributes)
        self.assert_having_at_most_one(Body)
        self.assert_having_at_most_one(Schema)


class ResourceGroup(Section):
    def parse_title(self):
        _, identifier = self.pop(0).astext().split(None, 1)
        self['identifier'] = identifier

    def validate(self):
        self.assert_having_only(Resource)


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

    def validate(self):
        self.assert_having_only((Parameters, Attributes, Model, Action))
        self.assert_having_at_most_one(Parameters)
        self.assert_having_at_most_one(Attributes)
        self.assert_having_at_most_one(Model)
        self.assert_having_at_least_one(Action)


class Model(Section):
    def parse_title(self):
        pass

    def validate(self):
        self.assert_having_only((Headers, Attributes, Body, Schema))
        self.assert_having_at_most_one(Headers)
        self.assert_having_at_most_one(Attributes)
        self.assert_having_at_most_one(Body)
        self.assert_having_at_most_one(Schema)


class Schema(AssetSection):
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

    def validate(self):
        self.assert_having_only((Relation, Parameters, Attributes, Request, Response))
        self.assert_having_at_most_one(Relation)
        self.assert_having_at_most_one(Parameters)
        self.assert_having_at_most_one(Attributes)
        self.assert_having_any(Request)
        self.assert_having_at_least_one(Response)


class ResourceAction(Resource, Action):
    def parse_title(self):
        Action.parse_title(self)

    def parse_content(self):
        pass

    def validate(self):
        Action.validate(self)


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
    def validate(self):
        self.assert_having_no_sections()


class Attributes(Section):
    def parse_title(self):
        pass

    def validate(self):
        pass  # TODO: assert MSON type definitions


class Headers(Section):
    def __init__(self, **kwargs):
        self.headers = []
        Section.__init__(self, **kwargs)

    def parse_content(self):
        for header in self.pop(0).astext().splitlines():
            self.headers.append(header.strip())

    def validate(self):
        assert len(self) == 2 and isinstance(self[1], (nodes.literal_block, nodes.paragraph)), \
            "Headers section should have only literal block"


class Body(AssetSection):
    pass


class DataStructures(Section):
    def parse_content(self):
        for node in self:
            if isinstance(node, nodes.section):
                self.parse_section(node)

    def parse_section(self, node):
        matched = re.search('^(.*?)\s*\((.*)\)\s*$', node[0].astext())
        if not matched:
            return

        objname = matched.group(1).strip()
        typename = matched.group(2).strip()

        desc = sphinxnodes.desc(domain='js', desctype='data', objtype='data')
        sig = sphinxnodes.desc_signature(object='', fullname=objname, first=False)
        sig['names'].append(objname)
        sig['ids'].append(objname.replace('$', '_S_'))
        sig += sphinxnodes.desc_name(text="%s (%s)" % (objname, typename))

        content = sphinxnodes.desc_content()
        node.pop(0)
        transpose_subnodes(node, content)

        node.replace_self(desc)
        desc.append(sig)
        desc.append(content)

    def validate(self):
        pass  # TODO: assert MSON type definitions


class Relation(Section):
    def validate(self):
        self.assert_having_no_sections()
