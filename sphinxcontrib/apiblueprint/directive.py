# -*- coding: utf-8 -*-
import io
import os
import re
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive
from recommonmark.parser import CommonMarkParser
from sphinxcontrib.apiblueprint.translator import translate


def relfn2path(env, relpath, filename):
    if filename.startswith('/') or filename.startswith(os.sep):
        relfn = filename[1:]
    else:
        relfn = os.path.join(os.path.dirname(relpath), filename)

    relfn = os.path.normpath(relfn)
    return relfn, os.path.join(env.srcdir, relfn)


class ApiBlueprintDirective(Directive):
    has_content = False
    required_arguments = 1

    def run(self):
        self.env = self.state.document.settings.env
        docpath = self.env.doc2path(self.env.docname, base=None)
        relfn, abspath = relfn2path(self.env, docpath, self.arguments[0])

        content = self.read_markdown(relfn, abspath, [])
        doctree = publish_doctree(content, parser=CommonMarkParser())
        translate(doctree)

        return doctree[:]

    def read_markdown(self, relfn, abspath, included):
        if abspath in included:
            raise self.error('Infinite include loop has detected. check your API definitions.')

        try:
            with io.open(abspath, 'r', encoding='utf-8-sig') as fd:
                content = fd.read()
                self.env.note_dependency(relfn)
        except IOError as exc:
            raise self.error('Fail to read API Blueprint: %s' % exc)

        parts = re.split('<!--\s+include\(([^)]+)\)\s+-->', content, re.M)
        for i in range(len(parts) // 2):
            filename = parts[i * 2 + 1]

            relfn_included, abspath_included = relfn2path(self.env, relfn, filename)
            parts[i * 2 + 1] = self.read_markdown(relfn_included, abspath_included, included + [abspath])

        return "".join(parts)
