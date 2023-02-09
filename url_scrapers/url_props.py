from enum import Enum

class CanUseRawHTMLRequests(Enum):
    No = -1
    Unknown = 0
    Yes = 1

class UrlProps():
    '''A class for determining characteristics of a url:
        - does the url require a browser emulator to render correctly using js
        - are there anchor tag refs on the page
        - are there cookies to agree on the page
        - are there scripts to load on the page
        '''

    def __init__(self, anchorTagHrefs: list[str] = [], embeddedScriptAndAnchorTagHrefs: list[str] = [], cookiesAgreed: bool = False) -> None:
        self.canUseRawHTMLRequests: CanUseRawHTMLRequests = CanUseRawHTMLRequests.Unknown
        self.anchorTagHrefs = anchorTagHrefs
        self.embeddedScriptAndAnchorTagHrefs = embeddedScriptAndAnchorTagHrefs
        self.cookiesAgreed = cookiesAgreed

    def getNumAnchorTags(self):
        return len(self.anchorTagHrefs)

    def getNumHrefsInScriptsAndButtons(self):
        return len(self.embeddedScriptAndAnchorTagHrefs)
    numAnchorTags = property(getNumAnchorTags)
    numHrefsInScriptsAndButtons = property(getNumHrefsInScriptsAndButtons)
