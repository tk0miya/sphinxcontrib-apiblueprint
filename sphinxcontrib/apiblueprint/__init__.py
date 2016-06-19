# -*- coding: utf-8 -*-
from sphinxcontrib.apiblueprint.directive import ApiBlueprintDirective


def setup(app):
    app.add_directive('apiblueprint', ApiBlueprintDirective)
    app.setup_extension('sphinxcontrib.httpdomain')
