# -*- coding: utf-8 -*-
import io
import os
import re
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive
from recommonmark.parser import CommonMarkParser
from sphinxcontrib.apiblueprint.translator import translate


def relfn2path(srcdir, relpath, filename):
    if filename.startswith('/') or filename.startswith(os.sep):
        relfn = filename[1:]
    else:
        relfn = os.path.join(os.path.dirname(relpath), filename)

    relfn = os.path.normpath(relfn)
    return relfn, os.path.join(srcdir, relfn)


class MarkdownReader(object):
    INCLUDE_STMT = re.compile('([ \t]*)<!--\s+include\(([^)]+)\)\s+-->', re.M)

    def __init__(self, srcdir):
        self.processed = set()
        self.srcdir = srcdir

    def read(self, relfn, abspath, included):
        if abspath in included:
            raise RuntimeError('Infinite include loop has detected. check your API definitions.')

        with io.open(abspath, 'r', encoding='utf-8-sig') as fd:
            content = fd.read()
            self.processed.add(relfn)

        parts = self.INCLUDE_STMT.split(content)
        for i in range(len(parts) // 3):
            indent = parts[i * 3 + 1]
            filename = parts[i * 3 + 2]

            relfn_included, abspath_included = relfn2path(self.srcdir, relfn, filename)
            replaced = self.read(relfn_included, abspath_included, included + [abspath])
            parts[i * 3 + 2] = ("\n" + indent).join(replaced.splitlines())

        return "".join(parts)


class ApiBlueprintDirective(Directive):
    has_content = False
    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        self.env = self.state.document.settings.env
        docpath = self.env.doc2path(self.env.docname, base=None)
        relfn, abspath = relfn2path(self.env.srcdir, docpath, self.arguments[0])

        try:
            reader = MarkdownReader(self.env.srcdir)
            content = reader.read(relfn, abspath, [])
            for fn in reader.processed:
                self.env.note_dependency(fn)
            doctree = publish_doctree(content, parser=CommonMarkParser(),
                                      settings_overrides={'doctitle_xform': False})
            translate(self.env, doctree)

            return doctree[:]
        except RuntimeError as exc:
            raise self.error(exc.message)
        except IOError as exc:
            raise self.error('Fail to read API Blueprint: %s' % exc)
