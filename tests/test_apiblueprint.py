# -*- coding: utf-8 -*-
import unittest
from time import time
from docutils import nodes
from functools import wraps
from textwrap import dedent


# export docstring to markdown file automatically
def with_app(**sphinxkwargs):
    def decorator(func):
        from sphinx_testing import with_app

        @wraps(func)
        @with_app(**sphinxkwargs)
        def decorated(self, app, status, warnings):
            if func.__doc__:
                (app.srcdir / 'api.md').write_text(dedent(func.__doc__))

            func(self, app, status, warnings)

        return decorated

    return decorator


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
        self.assertIn('ERROR: Infinite include loop has detected. check your API definitions.', warnings.getvalue())

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

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_simple_apiblueprint(self, app, status, warnings):
        """
        # GET /message
        + Response 200 (text/plain)

                Hello World!
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'GET /message')
        self.assertEqual(blueprint[1][0].astext(), 'Response 200')
        self.assertEqual(blueprint[1][1][0].astext(), 'Headers:')
        self.assertEqual(blueprint[1][1][1].astext(), 'Content-Type: text/plain')
        self.assertIsInstance(blueprint[1][1][1], nodes.literal_block)
        self.assertEqual(blueprint[1][2][0].astext(), 'Body:')
        self.assertEqual(blueprint[1][2][1].astext(), 'Hello World!')
        self.assertIsInstance(blueprint[1][2][1], nodes.literal_block)

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_description_for_response(self, app, status, warnings):
        """
        # GET /message
        + Response 200 (text/plain)
            Description of Response

            + Body

                  Hello World!
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'GET /message')
        self.assertEqual(blueprint[1][0].astext(), 'Response 200')
        self.assertEqual(blueprint[1][1].astext(), 'Description of Response')
        self.assertEqual(blueprint[1][2][0].astext(), 'Headers:')
        self.assertEqual(blueprint[1][2][1].astext(), 'Content-Type: text/plain')
        self.assertEqual(blueprint[1][3][0].astext(), 'Body:')
        self.assertEqual(blueprint[1][3][1].astext(), 'Hello World!')
        self.assertIsInstance(blueprint[1][3][1], nodes.literal_block)

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_response_header_section(self, app, status, warnings):
        """
        # GET /message
        + Response 200 (text/plain)
            + Headers

                  Accept-Language: ja

            + Body

                  Hello World!
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'GET /message')
        self.assertEqual(blueprint[1][0].astext(), 'Response 200')
        self.assertEqual(blueprint[1][1][0].astext(), 'Headers:')
        self.assertEqual(blueprint[1][1][1].astext(), ('Content-Type: text/plain\n'
                                                       'Accept-Language: ja'))
        self.assertIsInstance(blueprint[1][1][1], nodes.literal_block)
        self.assertEqual(blueprint[1][2][0].astext(), 'Body:')
        self.assertEqual(blueprint[1][2][1].astext(), 'Hello World!')
        self.assertIsInstance(blueprint[1][2][1], nodes.literal_block)

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_resource_group(self, app, status, warnings):
        """
        # Group Blog Posts
        ## GET /posts/{id}
        + Response 200 (text/plain)

            Hello World!

        ## POST /posts
        + Parameters
            + message (string, required)

        + Response 200 (text/plain)

            OK
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'Blog Posts')
        self.assertEqual(blueprint[1][0].astext(), 'GET /posts/{id}')
        self.assertEqual(blueprint[1][1][2][1].astext(), 'Hello World!')
        self.assertEqual(blueprint[2][0].astext(), 'POST /posts')
        self.assertEqual(blueprint[2][1][0].astext(), 'Parameters:')
        self.assertEqual(blueprint[2][1][1].astext(), 'message (string, required)')
        self.assertEqual(blueprint[2][2][0].astext(), 'Response 200')
        self.assertEqual(blueprint[2][2][2][1].astext(), 'OK')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_action(self, app, status, warnings):
        """
        # Blog Posts [/posts]
        ## Retrieve Blog Posts [GET]
        + Response 200 (text/plain)

            Hello World!

        ## Create a new Post [POST]
        + Parameters
            + message (string, required)

        + Response 200 (text/plain)

            OK
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'Blog Posts')
        self.assertEqual(blueprint[1][0].astext(), 'GET /posts (Retrieve Blog Posts)')
        self.assertEqual(blueprint[1][1][2][1].astext(), 'Hello World!')
        self.assertEqual(blueprint[2][0].astext(), 'POST /posts (Create a new Post)')
        self.assertEqual(blueprint[2][1][0].astext(), 'Parameters:')
        self.assertEqual(blueprint[2][1][1].astext(), 'message (string, required)')
        self.assertEqual(blueprint[2][2][0].astext(), 'Response 200')
        self.assertEqual(blueprint[2][2][2][1].astext(), 'OK')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_request(self, app, status, warnings):
        """
        # Blog Post [/posts]
        ## Create a new Post [POST]
        + Request (application/json)
            + Body

              {
                "message": "hello world"
              }

        + Response 200 (text/plain)

            OK
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'Blog Post [/posts]')
        self.assertEqual(blueprint[1].astext(), 'Create a new Post [POST]')
        self.assertEqual(blueprint[2][0].astext(), 'Request')
        self.assertEqual(blueprint[2][1][0].astext(), 'Headers:')
        self.assertEqual(blueprint[2][1][1].astext(), 'Content-Type: application/json')
        self.assertEqual(blueprint[2][2][0].astext(), 'Body:')
        self.assertEqual(blueprint[2][2][1].astext(), '{\n"message": "hello world"\n}')
        self.assertEqual(blueprint[3][0].astext(), 'Response 200')
        self.assertEqual(blueprint[3][2][1].astext(), 'OK')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_request_having_identifier(self, app, status, warnings):
        """
        # Blog Post [/posts]
        ## Create a new Post [POST]
        + Request Create a new Post (application/json)
            + Body

              {
                "message": "hello world"
              }

        + Response 200 (text/plain)

            OK
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'Blog Post [/posts]')
        self.assertEqual(blueprint[1].astext(), 'Create a new Post [POST]')
        self.assertEqual(blueprint[2][0].astext(), 'Request Create a new Post')
        self.assertEqual(blueprint[2][1][0].astext(), 'Headers:')
        self.assertEqual(blueprint[2][1][1].astext(), 'Content-Type: application/json')
        self.assertEqual(blueprint[2][2][0].astext(), 'Body:')
        self.assertEqual(blueprint[2][2][1].astext(), '{\n"message": "hello world"\n}')
        self.assertEqual(blueprint[3][0].astext(), 'Response 200')
        self.assertEqual(blueprint[3][2][1].astext(), 'OK')
