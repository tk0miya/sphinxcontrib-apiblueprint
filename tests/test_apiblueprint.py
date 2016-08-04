# -*- coding: utf-8 -*-
import unittest
from time import time
from docutils import nodes
from functools import wraps
from textwrap import dedent
from sphinx import addnodes


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
    def test_include(self, app, status, warnings):
        # prepare
        (app.srcdir / 'api.md').write_text(
            "This is Markdown document\n"
            "<!-- include(subdoc1.md) -->\n"
            "\n"
            "    <!-- include(subdoc2.md) -->\n"
        )
        (app.srcdir / 'subdoc1.md').write_text(
            "This is sub1 document\n"
            "Line1-2\n"
        )
        (app.srcdir / 'subdoc2.md').write_text(
            "This is sub2 document\n"
            "Line2-2\n"
        )

        app.build()
        print(status.getvalue(), warnings.getvalue())
        content = app.env.get_doctree('index')[0]
        self.assertIsInstance(content[0], nodes.title)
        self.assertIsInstance(content[1], nodes.paragraph)
        self.assertIsInstance(content[2], nodes.literal_block)
        self.assertEqual(content[0].astext(), "Example API")
        self.assertEqual(content[1].astext(), ("This is Markdown document\n"
                                               "This is sub1 document\nLine1-2"))
        self.assertEqual(content[2].astext(), ("This is sub2 document\nLine2-2"))

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
    def test_simple_apiblueprint(self, app, status, warnings):
        """
        # GET /message
        + Response 200 (text/plain)

                Hello World!
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        desc = app.env.get_doctree('index')[0][1]
        self.assertIsInstance(desc, addnodes.desc)
        self.assertIsInstance(desc[0], addnodes.desc_signature)
        self.assertIsInstance(desc[1], addnodes.desc_content)

        signature = desc[0]
        self.assertEqual(signature.astext(), 'GET /message')
        self.assertIsInstance(signature[0], addnodes.desc_name)

        content = desc[1]
        self.assertEqual(content[0][0].astext(), 'Response 200')
        self.assertEqual(content[0][1][0].astext(), 'Headers:')
        self.assertEqual(content[0][1][1].astext(), 'Content-Type: text/plain')
        self.assertIsInstance(content[0][1][1], nodes.literal_block)
        self.assertEqual(content[0][2][0].astext(), 'Body:')
        self.assertEqual(content[0][2][1].astext(), 'Hello World!')
        self.assertIsInstance(content[0][2][1], nodes.literal_block)

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

        desc = app.env.get_doctree('index')[0][1]
        self.assertIsInstance(desc, addnodes.desc)
        self.assertIsInstance(desc[0], addnodes.desc_signature)
        self.assertIsInstance(desc[1], addnodes.desc_content)

        signature = desc[0]
        self.assertEqual(signature.astext(), 'GET /message')
        self.assertIsInstance(signature[0], addnodes.desc_name)

        content = desc[1]
        self.assertEqual(content[0][0].astext(), 'Response 200')
        self.assertEqual(content[0][1].astext(), 'Description of Response')
        self.assertEqual(content[0][2][0].astext(), 'Headers:')
        self.assertEqual(content[0][2][1].astext(), 'Content-Type: text/plain')
        self.assertEqual(content[0][3][0].astext(), 'Body:')
        self.assertEqual(content[0][3][1].astext(), 'Hello World!')

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

        desc = app.env.get_doctree('index')[0][1]
        self.assertIsInstance(desc, addnodes.desc)
        self.assertIsInstance(desc[0], addnodes.desc_signature)
        self.assertIsInstance(desc[1], addnodes.desc_content)

        signature = desc[0]
        self.assertEqual(signature.astext(), 'GET /message')
        self.assertIsInstance(signature[0], addnodes.desc_name)

        content = desc[1]
        self.assertEqual(content[0][0].astext(), 'Response 200')
        self.assertEqual(content[0][1][0].astext(), 'Headers:')
        self.assertEqual(content[0][1][1].astext(), ('Accept-Language: ja\n'
                                                     'Content-Type: text/plain'))
        self.assertIsInstance(content[0][1][1], nodes.literal_block)
        self.assertEqual(content[0][2][0].astext(), 'Body:')
        self.assertEqual(content[0][2][1].astext(), 'Hello World!')
        self.assertIsInstance(content[0][2][1], nodes.literal_block)

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_empty_response(self, app, status, warnings):
        """
        # POST /message
        + Response 204
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'POST /message')
        self.assertEqual(blueprint[1].astext(), 'Response 204')

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

        get = blueprint[1]
        self.assertEqual(get[0].astext(), 'GET /posts/{id}')
        self.assertEqual(get[1][0][2][1].astext(), 'Hello World!')

        post = blueprint[2]
        self.assertEqual(post[0].astext(), 'POST /posts')
        self.assertEqual(post[1][0][0].astext(), 'Parameters:')
        self.assertEqual(post[1][0][1].astext(), 'message (string, required)')
        self.assertEqual(post[1][1][0].astext(), 'Response 200')
        self.assertEqual(post[1][1][2][1].astext(), 'OK')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_model(self, app, status, warnings):
        """
        # Blog Posts [/posts]

        + Model (text/plain)
            + Body
                Hello World!

        ## Retrieve blog posts [GET]

        + Response 200

            [Blog Posts][]
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]

        self.assertEqual(blueprint[0].astext(), 'Blog Posts')

        model = blueprint[1]
        self.assertEqual(model[0].astext(), 'Model (text/plain)')
        self.assertEqual(model[1][1].astext(), 'Hello World!')

        retrieve = blueprint[2]
        print retrieve[1][0]
        self.assertEqual(retrieve[0].astext(), 'GET /posts (Retrieve blog posts)')
        self.assertEqual(retrieve[1][0][1][1].astext(), '[Blog Posts][]')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_action(self, app, status, warnings):
        """
        # Blog Posts [/posts]
        ## GET
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

        get = blueprint[1]
        self.assertEqual(get[0].astext(), 'GET /posts')
        self.assertEqual(get[1][0][2][1].astext(), 'Hello World!')

        post = blueprint[2]
        self.assertEqual(post[0].astext(), 'POST /posts (Create a new Post)')
        self.assertEqual(post[1][0][0].astext(), 'Parameters:')
        self.assertEqual(post[1][0][1].astext(), 'message (string, required)')
        self.assertEqual(post[1][1][0].astext(), 'Response 200')
        self.assertEqual(post[1][1][2][1].astext(), 'OK')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_action_having_uri(self, app, status, warnings):
        """
        # Retrieve Blog Posts [GET /posts]
        + Response 200 (text/plain)

            Hello World!
        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]
        self.assertEqual(blueprint[0].astext(), 'GET /posts (Retrieve Blog Posts)')
        self.assertEqual(blueprint[1][0][0].astext(), 'Response 200')
        self.assertEqual(blueprint[1][0][2][1].astext(), 'Hello World!')

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
        self.assertEqual(blueprint[0].astext(), 'Blog Post')
        self.assertEqual(blueprint[1][0].astext(), 'POST /posts (Create a new Post)')

        request = blueprint[1][1][0]
        self.assertEqual(request[0].astext(), 'Request')
        self.assertEqual(request[1][0].astext(), 'Headers:')
        self.assertEqual(request[1][1].astext(), 'Content-Type: application/json')
        self.assertEqual(request[2][0].astext(), 'Body:')
        self.assertEqual(request[2][1].astext(), '{\n"message": "hello world"\n}')

        response = blueprint[1][1][1]
        self.assertEqual(response[0].astext(), 'Response 200')
        self.assertEqual(response[2][1].astext(), 'OK')

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
        self.assertEqual(blueprint[0].astext(), 'Blog Post')
        self.assertEqual(blueprint[1][0].astext(), 'POST /posts (Create a new Post)')

        request = blueprint[1][1][0]
        self.assertEqual(request[0].astext(), 'Request Create a new Post')
        self.assertEqual(request[1][0].astext(), 'Headers:')
        self.assertEqual(request[1][1].astext(), 'Content-Type: application/json')
        self.assertEqual(request[2][0].astext(), 'Body:')
        self.assertEqual(request[2][1].astext(), '{\n"message": "hello world"\n}')

        response = blueprint[1][1][1]
        self.assertEqual(response[0].astext(), 'Response 200')
        self.assertEqual(response[2][1].astext(), 'OK')

    @with_app(srcdir='tests/template', copy_srcdir_to_tmpdir=True)
    def test_data_structures(self, app, status, warnings):
        """
        # Data Structures
        ## Blog (object)

        + title (string)
        + author (string)

        ## Post (object)

        + blog_id (integer)
        + title (string)
        + message (string)

        """
        app.build()
        print(status.getvalue(), warnings.getvalue())

        blueprint = app.env.get_doctree('index')[0][1]

        self.assertEqual(blueprint[0].astext(), 'Data Structures')

        blog = blueprint[1]
        self.assertEqual(blog[0].astext(), 'Blog (object)')
        self.assertEqual(blog[1].astext(), 'title (string)\n\nauthor (string)')

        post = blueprint[2]
        self.assertEqual(post[0].astext(), 'Post (object)')
        self.assertEqual(post[1].astext(), 'blog_id (integer)\n\ntitle (string)\n\nmessage (string)')
