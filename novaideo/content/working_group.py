from zope.interface import implementer

from substanced.content import content
from substanced.util import renamer
from substanced.schema import NameSchemaNode

from dace.objectofcollaboration.entity import Entity
from dace.descriptors import SharedMultipleProperty, SharedUniqueProperty
from pontus.schema import omit
from pontus.core import VisualisableElement, VisualisableElementSchema

from .proposal import ProposalSchema, Proposal
from .interface import IWorkingGroup
from novaideo import _


def context_is_a_workinggroup(context, request):
    return request.registry.content.istype(context, 'workinggroup')


class WorkingGroupSchema(VisualisableElementSchema):

    name = NameSchemaNode(
        editing=context_is_a_workinggroup,
        )


@content(
    'workinggroup',
    icon='glyphicon glyphicon-align-left',
    )
@implementer(IWorkingGroup)
class WorkingGroup(VisualisableElement, Entity):
    name = renamer()
    template = 'pontus:templates/visualisable_templates/object.pt'
    proposal = SharedUniqueProperty('proposal', 'working_group')
    members = SharedMultipleProperty('members', 'working_groups')
