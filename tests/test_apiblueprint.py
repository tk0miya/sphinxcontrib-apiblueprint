# -*- coding: utf-8 -*-
import unittest
from time import time
from docutils import nodes
from sphinx_testing import with_app


class TestCase(unittest.TestCase):
    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_note_dependency(self, app, status, warnings):
        # prepare
        (app.srcdir / 'api.md').write_text(
            "This is *Markdown* document\n"
            "<!-- include(subdir/subdoc.md) -->"
        )
        (app.srcdir / 'subdir').makedirs()
        (app.srcdir / 'subdir' / 'subdoc.md').write_text(
            "This is *sub* document\n"
            "<!-- include(../subsubdoc.md) -->"
        )
        (app.srcdir / 'subsubdoc.md').write_text(
            "This is *subsub* document"
        )

        # first build
        app.build()

        # second build (no updates)
        status.truncate(0)
        warnings.truncate(0)
        app.build()

        self.assertIn('0 added, 0 changed, 0 removed', status.getvalue())

        # thrid build (.md file has changed)
        status.truncate(0)
        warnings.truncate(0)
        (app.srcdir / 'api.md').utime((time() + 1, time() + 1))
        app.build()

        self.assertIn('0 added, 1 changed, 0 removed', status.getvalue())

        # fourth build (included .md file has changed)
        status.truncate(0)
        warnings.truncate(0)
        (app.srcdir / 'subsubdoc.md').utime((time() + 1, time() + 1))
        app.build()

        self.assertIn('0 added, 1 changed, 0 removed', status.getvalue())

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_detect_infinit_include_loop(self, app, status, warnings):
        # prepare
        (app.srcdir / 'api.md').write_text(
            "This is *Markdown* document\n"
            "<!-- include(subdir/subdoc.md) -->"
        )
        (app.srcdir / 'subdir').makedirs()
        (app.srcdir / 'subdir' / 'subdoc.md').write_text(
            "This is *sub* document\n"
            "<!-- include(../subsubdoc.md) -->"
        )
        (app.srcdir / 'subsubdoc.md').write_text(
            "This is *subsub* document\n"
            "<!-- include(api.md) -->"
        )

        app.build()
        print(status.getvalue(), warnings.getvalue())
        self.assertIn('ERROR: Infinit include loop has detected. check your API definitions.', warnings.getvalue())

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_target_not_found(self, app, status, warnings):
        (app.srcdir / 'api.md').unlink()
        app.build()
        print(status.getvalue(), warnings.getvalue())
        self.assertIn('ERROR: Fail to read API Blueprint: [Errno 2] No such file or directory:', warnings.getvalue())

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_included_file_not_found(self, app, status, warnings):
        (app.srcdir / 'api.md').write_text(
            "This is *Markdown* document\n"
            "<!-- include(subdoc.md) -->"
        )
        app.build()
        print(status.getvalue(), warnings.getvalue())
        self.assertIn('ERROR: Fail to read API Blueprint: [Errno 2] No such file or directory:', warnings.getvalue())

    @with_app(srcdir='tests/template')
    def test_markdown(self, app, status, warnings):
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'GET /message')
        self.assertEqual(blueprint[1][0].astext(), 'Response 200')
        self.assertEqual(blueprint[1][1][0].astext(), 'Headers:')
        self.assertEqual(blueprint[1][1][1].astext(), 'Content-Type: text/plain')
        self.assertIsInstance(blueprint[1][1][1], nodes.literal_block)
        self.assertEqual(blueprint[1][2][0].astext(), 'Body:')
        self.assertEqual(blueprint[1][2][1].astext(), '  Hello World!')
        self.assertIsInstance(blueprint[1][2][1], nodes.literal_block)
