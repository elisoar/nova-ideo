# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import colander
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.form import FormView
from pontus.schema import Schema
from pontus.widget import FileWidget
from pontus.file import ObjectData, File

from novaideo.content.processes.organization_management.behaviors import (
    AddOrganizations)
from novaideo.content.novaideo_application import NovaIdeoApplication
from novaideo import _


class AddOrganizationsSchema(Schema):

    file = colander.SchemaNode(
            ObjectData(File),
            widget=FileWidget(),
            title=_('The xls file')
            )


@view_config(
    name='add_organizations',
    context=NovaIdeoApplication,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class AddOrganizationsView(FormView):

    title = _('Upload organizations')
    schema = AddOrganizationsSchema(editable=True)
    behaviors = [AddOrganizations]
    formid = 'formaddorganization'
    name = 'add_organizations'


DEFAULTMAPPING_ACTIONS_VIEWS.update({AddOrganizations:AddOrganizationsView})