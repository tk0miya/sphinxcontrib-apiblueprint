# -*- coding: utf-8 -*-
import re
from docutils import nodes

# HTTP methods (from RFC7231)
HTTP_METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "CONNECT", "OPTIONS", "TRACE"]

# URI Template
URI_TEMPLATE = re.compile('^/\S+$')


def get_children(node, cls):
    return [subnode for subnode in node if isinstance(subnode, cls)]


def replace_nodeclass(node, cls):
    newnode = cls(**node.attributes)
    transpose_subnodes(node, newnode)
    node.replace_self(newnode)

    return newnode


def transpose_subnodes(old, new):
    for subnode in old[:]:
        old.remove(subnode)
        new += subnode


def extract_option(title):
    matched = re.search('\[(.*)\]$', title)
    if matched is None:
        return None
    else:
        return matched.group(1)


def detect_section_type(entity, node):
    title = node[0].astext().splitlines()[0].strip()
    if entity == 'header':
        return detect_header_section_type(title)
    else:
        return detect_list_section_type(title)


def detect_header_section_type(title):
    from sphinxcontrib.apiblueprint import addnodes

    leading_word = title.split()[0]
    option = extract_option(title) or ''

    if title == 'Data Structures':
        return addnodes.DataStructures
    elif leading_word == 'Group':
        return addnodes.ResourceGroup
    elif title in HTTP_METHODS:
        # <HTTP request method>  => Action section
        return addnodes.Action
    elif option in HTTP_METHODS:
        # <identifier> [<HTTP request method>] => Action section
        return addnodes.Action
    elif leading_word in HTTP_METHODS:
        # <HTTP request method> <URI template> => ResourceAction section
        #
        # Note: Originally, this is a Resource section which represents
        # the Action section
        return addnodes.ResourceAction
    elif URI_TEMPLATE.match(title):
        # <URI template>  => Resource section
        return addnodes.Resource
    elif URI_TEMPLATE.match(option):
        # <identifier> [<URI template>] => Resource section
        return addnodes.Resource
    elif option:
        method, uri = option.split(None, 1)
        if method in HTTP_METHODS and URI_TEMPLATE.match(uri):
            # <identifier> [<HTTP request method> <URI template>] => ResourceAction section
            #
            # Note: Same as above. this is a Resource and Action at same time
            return addnodes.ResourceAction
        else:
            return None


def detect_list_section_type(title):
    from sphinxcontrib.apiblueprint import addnodes

    single_keywords = {
        'Schema': addnodes.Schema,
        'Parameters': addnodes.Parameters,
        'Headers': addnodes.Headers,
        'Body': addnodes.Body,
    }
    leading_keywords = {
        "Model": addnodes.Model,
        "Request": addnodes.Request,
        "Response": addnodes.Response,
        "Attributes": addnodes.Attributes,
        "Relation:": addnodes.Relation,
    }

    leading_word = title.split()[0]
    if title in single_keywords:
        return single_keywords[title]
    elif leading_word in leading_keywords:
        return leading_keywords[leading_word]
    else:
        return None


def split_title_and_content(node):
    if len(node[0]) > 1 and node[0][1] == '\n':
        title = node[0].pop(0)
        node[0].pop(0)  # Remove return char
        node.insert(0, nodes.title(text=title))
