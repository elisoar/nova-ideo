# Copyright (c) 2014 by Ecreall under licence AGPL terms
# avalaible on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi
"""
This module represent the Comment management process definition
powered by the dace engine. This process is unique, which means that
this process is instantiated only once.
"""
from dace.processdefinition.processdef import ProcessDefinition
from dace.processdefinition.activitydef import ActivityDefinition
from dace.processdefinition.gatewaydef import (
    ExclusiveGatewayDefinition,
    ParallelGatewayDefinition)
from dace.processdefinition.transitiondef import TransitionDefinition
from dace.processdefinition.eventdef import (
    StartEventDefinition,
    EndEventDefinition)
from dace.objectofcollaboration.services.processdef_container import (
    process_definition)
from pontus.core import VisualisableElement

from .behaviors import (
    Respond,
    Edit,
    Remove,
    Pin,
    Unpin,
    TransformToIdea)
from novaideo import _


@process_definition(name='commentmanagement', id='commentmanagement')
class CommentManagement(ProcessDefinition, VisualisableElement):
    isUnique = True

    def __init__(self, **kwargs):
        super(CommentManagement, self).__init__(**kwargs)
        self.title = _('Comment management')
        self.description = _('Comment management')

    def _init_definition(self):
        self.defineNodes(
                start = StartEventDefinition(),
                pg = ParallelGatewayDefinition(),
                respond = ActivityDefinition(contexts=[Respond],
                                       description=_("Respond"),
                                       title=_("Respond"),
                                       groups=[]),
                edit = ActivityDefinition(contexts=[Edit],
                                       description=_("Edit"),
                                       title=_("Edit"),
                                       groups=[]),
                remove = ActivityDefinition(contexts=[Remove],
                                       description=_("Remove"),
                                       title=_("Remove"),
                                       groups=[]),
                pin = ActivityDefinition(contexts=[Pin],
                                       description=_("Pin"),
                                       title=_("Pin"),
                                       groups=[]),
                unpin = ActivityDefinition(contexts=[Unpin],
                                       description=_("Unpin"),
                                       title=_("Unpin"),
                                       groups=[]),
                transformtoidea = ActivityDefinition(contexts=[TransformToIdea],
                                       description=_("Transform a comment into an idea"),
                                       title=_("Transform into an idea"),
                                       groups=[]),
                eg = ExclusiveGatewayDefinition(),
                end = EndEventDefinition(),
        )
        self.defineTransitions(
                TransitionDefinition('start', 'pg'),
                TransitionDefinition('pg', 'respond'),
                TransitionDefinition('respond', 'eg'),
                TransitionDefinition('pg', 'transformtoidea'),
                TransitionDefinition('transformtoidea', 'eg'),
                TransitionDefinition('pg', 'edit'),
                TransitionDefinition('edit', 'eg'),
                TransitionDefinition('pg', 'remove'),
                TransitionDefinition('remove', 'eg'),
                TransitionDefinition('pg', 'pin'),
                TransitionDefinition('pin', 'eg'),
                TransitionDefinition('pg', 'unpin'),
                TransitionDefinition('unpin', 'eg'),
                TransitionDefinition('eg', 'end'),
        )
