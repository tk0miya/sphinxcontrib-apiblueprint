import unittest
from docutils import nodes
from sphinxcontrib.apiblueprint import addnodes
from sphinxcontrib.apiblueprint.utils import detect_section_type


class TestCase(unittest.TestCase):
    def test_detect_section_type(self):
        def node2title(title):
            section = nodes.section()
            section += nodes.title(text=title)
            return section

        title = 'Group Blog Posts'
        self.assertEqual(addnodes.ResourceGroup, detect_section_type(node2title(title)))

        title = '/posts/{id}'
        self.assertEqual(addnodes.Resource, detect_section_type(node2title(title)))

        title = 'Blog Posts [/posts/{id}]'
        self.assertEqual(addnodes.Resource, detect_section_type(node2title(title)))

        title = 'GET /posts/{id}'
        self.assertEqual(addnodes.Resource, detect_section_type(node2title(title)))

        title = 'Blog Posts [GET /posts/{id}]'
        self.assertEqual(addnodes.Resource, detect_section_type(node2title(title)))

        title = 'Model (text/plain)'
        self.assertEqual(addnodes.Model, detect_section_type(node2title(title)))

        title = 'Schema'
        self.assertEqual(addnodes.Schema, detect_section_type(node2title(title)))

        title = 'GET'
        self.assertEqual(addnodes.Action, detect_section_type(node2title(title)))

        title = 'Retrieve Blog Posts [GET]'
        self.assertEqual(addnodes.Action, detect_section_type(node2title(title)))

        title = 'Delete a Post [DELETE /posts/{id}]'
        self.assertEqual(addnodes.Action, detect_section_type(node2title(title), inside_resource=True))

        title = 'Request Create Blog Post (application/json)'
        self.assertEqual(addnodes.Request, detect_section_type(node2title(title), inside_resource=True))

        title = 'Response 201 (application/json)'
        self.assertEqual(addnodes.Response, detect_section_type(node2title(title), inside_resource=True))

        title = 'Parameters'
        self.assertEqual(addnodes.Parameters, detect_section_type(node2title(title)))

        title = 'Attributes (object)'
        self.assertEqual(addnodes.Attributes, detect_section_type(node2title(title)))

        title = 'Headers'
        self.assertEqual(addnodes.Headers, detect_section_type(node2title(title)))

        title = 'Body'
        self.assertEqual(addnodes.Body, detect_section_type(node2title(title)))

        title = 'Data Structures'
        self.assertEqual(addnodes.DataStructures, detect_section_type(node2title(title)))

        title = 'Relation: task'
        self.assertEqual(addnodes.Relation, detect_section_type(node2title(title)))

        title = 'Unknown'
        self.assertEqual(None, detect_section_type(node2title(title)))

        http_methods = ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE"]
        for method in http_methods:
            self.assertEqual(addnodes.Action, detect_section_type(node2title(method)))
