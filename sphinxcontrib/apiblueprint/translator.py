# -*- coding: utf-8 -*-
from docutils import nodes
from sphinxcontrib.apiblueprint.utils import transpose_subnodes


class APIBlueprintTranslator(nodes.NodeVisitor):
    def warn(self, *args, **kwargs):
        self.document.reporter.warn(*args, **kwargs)

    def visit_document(self, node):
        if isinstance(node[0], nodes.title):
            # insert section node if doc has only ONE section
            section = nodes.section()
            section['ids'].append(nodes.make_id(node[0].astext()))
            transpose_subnodes(node, section)
            node += section

        raise nodes.SkipNode
