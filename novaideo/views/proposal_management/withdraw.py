
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.view import BasicView

from novaideo.content.processes.proposal_management.behaviors import  Withdraw
from novaideo.content.proposal import Proposal
from novaideo import _


@view_config(
    name='withdraw',
    context=Proposal,
    renderer='pontus:templates/view.pt',
    )
class WithdrawView(BasicView):
    title = _('Withdraw')
    name = 'withdraw'
    behaviors = [Withdraw]
    viewid = 'withdraw'


    def update(self):
        self.execute(None)        
        return list(self.behaviorinstances.values())[0].redirect(
                                       self.context, self.request)

DEFAULTMAPPING_ACTIONS_VIEWS.update({Withdraw:WithdrawView})
