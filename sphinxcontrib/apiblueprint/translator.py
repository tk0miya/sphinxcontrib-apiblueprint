# -*- coding: utf-8 -*-
from docutils import nodes
from sphinx import addnodes
from sphinxcontrib.apiblueprint.utils import (
    detect_section_type, replace_nodeclass, transpose_subnodes, split_title_and_content
)
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


class APIBlueprintTranslator(BaseNodeVisitor):
    """Translate naked doctree from recommonmark to API Blueprintbased doctree"""
    def visit_document(self, node):
        if isinstance(node[0], nodes.title):
            # insert section node if doc has only ONE section
            section = nodes.section()
            section['ids'].append(nodes.make_id(node[0].astext()))
            transpose_subnodes(node, section)
            node += section

    def depart_section(self, node):
        section_type = detect_section_type("header", node)
        if section_type:
            newnode = section_type.parse_node(node)
            node.replace_self(newnode)

    def depart_bullet_list(self, node):
        parent = node.parent
        for item in reversed(node):
            section_type = detect_section_type("list", item)
            if section_type:
                split_title_and_content(item)
                newnode = section_type.parse_node(item)
                node.remove(item)

                index = parent.index(node)
                parent.insert(index + 1, newnode)

        if len(node) == 0:
            parent.remove(node)


class APIBlueprintRepresenter(BaseNodeVisitor):
    """Translate API Bluerprint based doctree to common Sphinx doctree"""
    def depart_ResourceGroup(self, node):
        title = nodes.title(text=node['identifier'])
        node.insert(0, title)

        replace_nodeclass(node, nodes.section)

    def depart_Resource(self, node):
        if node['identifier']:
            node.insert(0, nodes.title(text=node['identifier']))
        else:
            node.insert(0, nodes.title(text=node['uri']))

        replace_nodeclass(node, nodes.section)

    def depart_Model(self, node):
        model = replace_nodeclass(node, nodes.section)
        model['ids'].append(nodes.make_id(model[0].astext()))

    def depart_Schema(self, node):
        title = nodes.paragraph(text='Schema:')
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

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

    def depart_ResourceAction(self, node):
        self.depart_Action(node)

    def depart_Request(self, node):
        title = nodes.paragraph()
        title += nodes.strong(text='Request')
        if node['identifier']:
            title += nodes.Text(' ' + node['identifier'])
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

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

    def depart_Attributes(self, node):
        bullet_list = nodes.bullet_list()
        bullet_list += nodes.list_item()
        transpose_subnodes(node, bullet_list[0])
        node.replace_self(bullet_list)

    def depart_Body(self, node):
        title = nodes.paragraph(text='Body:')
        node.insert(0, title)

        replace_nodeclass(node, nodes.container)

    def depart_DataStructures(self, node):
        for desc in node.traverse(addnodes.desc):
            name = desc[0]['names'][-1]
            self.env.domaindata['js']['objects'][name] = (self.env.docname, 'data')

        node.insert(0, nodes.title(text='Data Structures'))
        replace_nodeclass(node, nodes.section)

    def depart_Headers(self, node):
        node.append(nodes.paragraph(text='Headers:'))
        node.append(nodes.literal_block(text="\n".join(sorted(node.headers))))
        replace_nodeclass(node, nodes.container)


def translate(env, doctree):
    translator = APIBlueprintTranslator(env, doctree)
    doctree.walkabout(translator)
    representer = APIBlueprintRepresenter(env, doctree)
    doctree.walkabout(representer)
    return doctree
