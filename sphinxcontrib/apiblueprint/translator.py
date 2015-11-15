# -*- coding: utf-8 -*-
from docutils import nodes
from sphinxcontrib.apiblueprint import addnodes
from sphinxcontrib.apiblueprint.utils import detect_section_type, transpose_subnodes


def skipper(self, node):
    raise nodes.SkipNode


class APIBlueprintPreTranslator(nodes.NodeVisitor):
    # skipped nodes
    visit_title = skipper
    visit_paragraph = skipper
    visit_literal_block = skipper

    def warn(self, *args, **kwargs):
        self.document.reporter.warn(*args, **kwargs)

    def visit_document(self, node):
        if isinstance(node[0], nodes.title):
            # insert section node if doc has only ONE section
            section = nodes.section()
            section['ids'].append(nodes.make_id(node[0].astext()))
            transpose_subnodes(node, section)
            node += section

    def depart_document(self, node):
        pass

    def visit_section(self, node):
        section_type = detect_section_type(node)
        if section_type:
            newnode = section_type()
            transpose_subnodes(node, newnode)
            node.replace_self(newnode)

            newnode.walkabout(self)

    def depart_section(self, node):
        pass

    def visit_bullet_list(self, node):
        parent = node.parent
        for item in reversed(node):
            section_type = detect_section_type(item)
            if section_type:
                newnode = section_type()
                transpose_subnodes(item, newnode)
                node.remove(item)

                index = parent.index(node)
                parent.insert(index + 1, newnode)

                newnode.walkabout(self)

        if len(node) == 0:
            parent.remove(node)

        raise nodes.SkipNode

    def visit_list_item(self, node):
        pass

    def depart_list_item(self, node):
        pass

    def visit_Resource(self, node):
        node.parse_title()

    def depart_Resource(self, node):
        pass

    def visit_Response(self, node):
        node.parse_title()
        node.remove(node[0])

    def depart_Response(self, node):
        pass


class APIBlueprintPostTranslator(object):
    def __init__(self, document):
        self.document = document

    def translate(self):
        for node in self.document.traverse(addnodes.Resource):
            self.visit_Resource(node)

    def visit_Resource(self, node):
        section = nodes.section()
        section['ids'].append(nodes.make_id(node[0].astext()))
        transpose_subnodes(node, section)
        node.replace_self(section)

        for subnode in section.traverse(addnodes.Response):
            self.visit_Response(subnode)

    def visit_Response(self, node):
        response = nodes.container()
        response += nodes.paragraph()
        response[0] += nodes.strong(text='Response')
        response[0] += nodes.Text(' ')
        response[0] += nodes.literal(text=node['status_code'])

        if node['content_type']:
            headers = nodes.container()
            headers += nodes.paragraph(text='Headers:')
            headers += nodes.literal_block(text="Content-Type: %s" %
                                                node['content_type'])

            response += headers

        body = nodes.container()
        body += nodes.paragraph(text='Body:')
        body += node[:]

        response += body

        node.replace_self(response)


def translate(doctree):
    pre_translator = APIBlueprintPreTranslator(doctree)
    doctree.walkabout(pre_translator)
    post_translator = APIBlueprintPostTranslator(doctree)
    post_translator.translate()
    return doctree
