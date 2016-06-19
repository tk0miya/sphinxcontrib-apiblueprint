# -*- coding: utf-8 -*-
from docutils import nodes
from sphinx import addnodes
from sphinxcontrib.apiblueprint.utils import (
    detect_section_type, replace_nodeclass, transpose_subnodes, split_title_and_content
)
from sphinxcontrib.apiblueprint.addnodes import Action
from sphinxcontrib.httpdomain import http_resource_anchor


class BaseNodeVisitor(nodes.NodeVisitor):
    def __init__(self, env, *args):
        self.env = env
        nodes.NodeVisitor.__init__(self, *args)

    def warn(self, *args, **kwargs):
        self.document.reporter.warn(*args, **kwargs)

    def unknown_visit(self, node):
        pass

    def unknown_departure(self, node):
        pass


class APIBlueprintPreTranslator(BaseNodeVisitor):
    def visit_document(self, node):
        if isinstance(node[0], nodes.title):
            # insert section node if doc has only ONE section
            section = nodes.section()
            section['ids'].append(nodes.make_id(node[0].astext()))
            transpose_subnodes(node, section)
            node += section

    def visit_section(self, node):
        section_type = detect_section_type(node)
        if section_type:
            newnode = replace_nodeclass(node, section_type)
            newnode.walkabout(self)

    def visit_bullet_list(self, node):
        parent = node.parent
        for item in reversed(node):
            section_type = detect_section_type(item)
            if section_type:
                split_title_and_content(item)
                newnode = section_type()
                transpose_subnodes(item, newnode)
                node.remove(item)

                index = parent.index(node)
                parent.insert(index + 1, newnode)

                newnode.walkabout(self)

        if len(node) == 0:
            parent.remove(node)

        raise nodes.SkipNode

    def visit_ResourceGroup(self, node):
        node.parse_title()
        node.remove(node[0])

    def visit_Resource(self, node):
        node.parse_title()

    def depart_Resource(self, node):
        if len(node.traverse(Action)) == 0:
            action = replace_nodeclass(node, Action)
            action.remove(action[0])

    def visit_Action(self, node):
        node.parse_title()
        node.remove(node[0])

    def visit_Parameters(self, node):
        node.remove(node[0])

    def visit_Request(self, node):
        node.parse_title()
        node.remove(node[0])

    def visit_Response(self, node):
        node.parse_title()
        node.remove(node[0])

    def visit_Headers(self, node):
        node.remove(node[0])

    def visit_Body(self, node):
        node.remove(node[0])
        node.dedent()


class APIBlueprintPostTranslator(BaseNodeVisitor):
    def depart_ResourceGroup(self, node):
        title = nodes.title(text=node['identifier'])
        node.insert(0, title)

        replace_nodeclass(node, nodes.section)

    def visit_Resource(self, node):
        node.restruct()

    def depart_Resource(self, node):
        if node['has_action']:
            node[0].replace_self(nodes.title(text=node['identifier']))

        replace_nodeclass(node, nodes.section)

    def depart_Action(self, node):
        http_method = node['http_method']
        uri = node['uri']

        self.env.domaindata['http'][http_method.lower()][uri] = (self.env.docname, node['identifier'], False)
        desc = addnodes.desc(domain='http',
                             desctype=http_method.lower(),
                             objtype=http_method.lower())

        sig = addnodes.desc_signature(method=http_method.lower(), path=uri, first=False,
                                      fullname="%s %s" % (http_method, uri))
        sig['ids'].append(http_resource_anchor(http_method, uri))
        if node['identifier']:
            sig += addnodes.desc_name(text="%s %s (%s)" % (http_method, uri, node['identifier']))
        else:
            sig += addnodes.desc_name(text="%s %s" % (http_method, uri))

        content = addnodes.desc_content()
        transpose_subnodes(node, content)

        node.replace_self(desc)
        desc.append(sig)
        desc.append(content)

    def visit_Request(self, node):
        node.restruct()

    def depart_Request(self, node):
        title = nodes.paragraph()
        title += nodes.strong(text='Request')
        if node['identifier']:
            title += nodes.Text(' ' + node['identifier'])
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

    def visit_Response(self, node):
        node.restruct()

    def depart_Response(self, node):
        title = nodes.paragraph()
        title += nodes.strong(text='Response')
        title += nodes.Text(' ')
        title += nodes.literal(text=node['status_code'])
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

    def depart_Parameters(self, node):
        title = nodes.paragraph(text='Parameters:')
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

    def depart_Body(self, node):
        title = nodes.paragraph(text='Body:')
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

    def depart_Headers(self, node):
        title = nodes.paragraph(text='Headers:')
        node.insert(0, title)

        replace_nodeclass(node[1], nodes.literal_block)
        replace_nodeclass(node, nodes.container)


def translate(env, doctree):
    pre_translator = APIBlueprintPreTranslator(env, doctree)
    doctree.walkabout(pre_translator)
    post_translator = APIBlueprintPostTranslator(env, doctree)
    doctree.walkabout(post_translator)
    return doctree
