# -*- coding: utf-8 -*-
import unittest
from sphinx_testing import with_tmpdir
from sphinxcontrib.apiblueprint.directive import MarkdownReader


class TestCase(unittest.TestCase):
    @with_tmpdir
    def test_MarkdownReader(self, tmpdir):
        # prepare
        (tmpdir / 'api.md').write_text(
            "This is Markdown document\n"
            "<!-- include(subdoc1.md) -->\n"
            "\n"
            "    <!-- include(subdoc2.md) -->\n"
        )
        (tmpdir / 'subdoc1.md').write_text(
            "This is sub1 document\n"
            "Line1-2\n"
        )
        (tmpdir / 'subdoc2.md').write_text(
            "This is sub2 document\n"
            "Line2-2\n"
        )

        reader = MarkdownReader(tmpdir)
        content = reader.read('api.md', tmpdir / 'api.md', [])
        self.assertEqual(content, ("This is Markdown document\n"
                                   "This is sub1 document\nLine1-2\n\n"
                                   "    This is sub2 document\n    Line2-2\n"))
        self.assertEqual(reader.processed, set(('api.md', 'subdoc1.md', 'subdoc2.md')))

    @with_tmpdir
    def test_detect_infinit_include_loop(self, tmpdir):
        # prepare
        (tmpdir / 'api.md').write_text(
            "This is *Markdown* document\n"
            "<!-- include(subdir/subdoc.md) -->"
        )
        (tmpdir / 'subdir').makedirs()
        (tmpdir / 'subdir' / 'subdoc.md').write_text(
            "This is *sub* document\n"
            "<!-- include(../subsubdoc.md) -->"
        )
        (tmpdir / 'subsubdoc.md').write_text(
            "This is *subsub* document\n"
            "<!-- include(api.md) -->"
        )

        with self.assertRaises(RuntimeError):
            reader = MarkdownReader(tmpdir)
            reader.read('api.md', tmpdir / 'api.md', [])

    @with_tmpdir
    def test_target_not_found(self, tmpdir):
        with self.assertRaises(IOError):
            reader = MarkdownReader(tmpdir)
            reader.read('api.md', tmpdir / 'api.md', [])

    @with_tmpdir
    def test_included_file_not_found(self, tmpdir):
        (tmpdir / 'api.md').write_text(
            "This is *Markdown* document\n"
            "<!-- include(subdoc.md) -->"
        )

        with self.assertRaises(IOError):
            reader = MarkdownReader(tmpdir)
            reader.read('api.md', tmpdir / 'api.md', [])
