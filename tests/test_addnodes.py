# -*- coding: utf-8 -*-
import unittest
from docutils import nodes
from sphinxcontrib.apiblueprint import addnodes


class TestCase(unittest.TestCase):
    def test_assert_having_only(self):
        node = addnodes.Section()
        node.assert_having_only(addnodes.Action)
        node.assert_having_only((addnodes.Action, addnodes.Parameters))

        # standard nodes are ignored
        node += nodes.section()
        node += nodes.paragraph()
        node += nodes.bullet_list()
        node.assert_having_only(addnodes.Action)

        # success
        node += addnodes.Action()
        node.assert_having_only(addnodes.Action)

        node += addnodes.Parameters()
        node.assert_having_only((addnodes.Action, addnodes.Parameters))

        # failed
        with self.assertRaises(AssertionError):
            node.assert_having_only(addnodes.Action)

        # descendants are ignored
        node[0] += addnodes.Body()
        node.assert_having_only((addnodes.Action, addnodes.Parameters))

    def test_assert_having_no_sections(self):
        node = addnodes.Section()
        node.assert_having_no_sections()

        # standard nodes are ignored
        node += nodes.section()
        node += nodes.paragraph()
        node += nodes.bullet_list()
        node.assert_having_no_sections()

        # failed
        node += addnodes.Action()
        with self.assertRaises(AssertionError):
            node.assert_having_no_sections()

        # descendants are ignored
        node.pop()
        node[0] += addnodes.Parameters()
        node.assert_having_no_sections()

    def test_assert_having_at_most_one(self):
        node = addnodes.Section()

        # standard nodes are ignored
        node += nodes.section()
        node += nodes.paragraph()
        node += nodes.bullet_list()
        node.assert_having_at_most_one(addnodes.Action)

        # success
        node.assert_having_at_most_one(addnodes.Action)

        node += addnodes.Action()
        node.assert_having_at_most_one(addnodes.Action)

        # failed
        node += addnodes.Action()
        with self.assertRaises(AssertionError):
            node.assert_having_at_most_one(addnodes.Action)

        # descendants are ignored
        node.pop()
        node[0] += addnodes.Action()
        node.assert_having_at_most_one(addnodes.Action)

        # other sections are ignored
        node[0] += addnodes.Parameters()
        node[0] += addnodes.Body()
        node.assert_having_at_most_one(addnodes.Action)

    def test_assert_having_any(self):
        node = addnodes.Section()

        # standard nodes are ignored
        node += nodes.section()
        node += nodes.paragraph()
        node += nodes.bullet_list()
        node.assert_having_any(addnodes.Action)

        # success
        node.assert_having_any(addnodes.Action)  # no items

        node += addnodes.Action()
        node.assert_having_any(addnodes.Action)  # one item

        node += addnodes.Action()
        node.assert_having_any(addnodes.Action)  # two items

        # descendants are ignored
        node.pop()
        node[0] += addnodes.Action()
        node.assert_having_any(addnodes.Action)

        # other sections are ignored
        node[0] += addnodes.Parameters()
        node[0] += addnodes.Body()
        node.assert_having_any(addnodes.Action)

    def test_assert_at_least_one(self):
        node = addnodes.Section()

        # failed
        with self.assertRaises(AssertionError):
            node.assert_having_at_least_one(addnodes.Action)

        # success
        node += addnodes.Action()
        node.assert_having_at_least_one(addnodes.Action)  # one item

        node += addnodes.Action()
        node.assert_having_at_least_one(addnodes.Action)  # two items

        # standard nodes are ignored
        node += nodes.section()
        node += nodes.paragraph()
        node += nodes.bullet_list()
        node.assert_having_at_least_one(addnodes.Action)

        # descendants are ignored
        node.pop()
        node[0] += addnodes.Action()
        node.assert_having_at_least_one(addnodes.Action)

        # other sections are ignored
        node[0] += addnodes.Parameters()
        node[0] += addnodes.Body()
        node.assert_having_at_least_one(addnodes.Action)
