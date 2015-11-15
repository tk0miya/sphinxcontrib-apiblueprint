# -*- coding: utf-8 -*-
import re
from sphinxcontrib.apiblueprint import addnodes


def get_children(node, cls):
    return [subnode for subnode in node if isinstance(subnode, cls)]


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


def detect_section_type(node, inside_resource=False):
    single_keywords = {
        'Schema': addnodes.Schema,
        'Parameters': addnodes.Parameters,
        'Headers': addnodes.Headers,
        'Body': addnodes.Body,
        'Data Structures': addnodes.DataStructures,
    }
    leading_keywords = {
        "Group": addnodes.ResourceGroup,
        "Model": addnodes.Model,
        "Request": addnodes.Request,
        "Response": addnodes.Response,
        "Attributes": addnodes.Attributes,
        "Relation:": addnodes.Relation,
    }
    # HTTP methods (from RFC7231)
    http_methods = ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE"]
    # URI Template
    uri_template = re.compile('^/\S+$')

    try:
        title = node[0].astext().strip()
        leading_word = title.split()[0]
        option = extract_option(title)

        if title in single_keywords:
            return single_keywords[title]
        elif leading_word in leading_keywords:
            return leading_keywords[leading_word]
        elif title in http_methods:
            # <HTTP request method>  => Action section
            return addnodes.Action
        elif option in http_methods:
            # <identifier> [<HTTP request method>] => Action section
            return addnodes.Action
        elif leading_word in http_methods:
            # <HTTP request method> <URI template>  => Resource section
            return addnodes.Resource
        elif uri_template.match(title):
            # <URI template>  => Resource section
            return addnodes.Resource
        elif uri_template.match(option):
            # <identifier> [<URI template>] => Resource section
            return addnodes.Resource
        elif option:
            method, uri = option.split(None, 1)
            if method in http_methods and uri_template.match(uri):
                # <identifier> [<HTTP request method> <URI template>] => Resource or Action
                if inside_resource:
                    return addnodes.Action
                else:
                    return addnodes.Resource
            else:
                return None
    except:
        return None
