
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.view import BasicView

from novaideo.content.processes.proposal_management.behaviors import (
    ProofreadingDone)
from novaideo.content.proposal import Proposal
from novaideo import _


@view_config(
    name='proofreading',
    context=Proposal,
    renderer='pontus:templates/view.pt',
    )
class ProofreadingDoneView(BasicView):
    title = _('Proofreading done')
    name = 'proofreading'
    behaviors = [ProofreadingDone]
    viewid = 'proofreading'


    def update(self):
        self.execute(None)        
        return list(self.behaviorinstances.values())[0].redirect(
                                       self.context, self.request)


DEFAULTMAPPING_ACTIONS_VIEWS.update({ProofreadingDone:ProofreadingDoneView})
