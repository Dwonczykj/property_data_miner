import io
import os
import re
import warnings
from collections import defaultdict
from collections.abc import Sequence
from enum import Enum, IntEnum
from os import path
from pprint import pprint

import debugpy as debug
import matplotlib.pyplot as plt
import numpy as np
import requests

'''
This script contains functions to parse individual urls into their constituent paths and then add them any exisiting url ranking trees.
'''

URL_RE_PATTERN = r'^(?:(?P<protocol>http[s]?|ftp):\/)?\/?(?P<domain>[^:\/\s]+)(?:(?P<path>(?:(?:\/\w+)*)(?:\/[\w\-\.]+[^#?\s]+))(?P<query>.*)(?P<id>#[\w\-]+)?)?$'

class UrlMatchEnum(IntEnum):
    URL_DOMAIN = 1
    URL_PATH = 2
    URL_QUERY = 11
    URL_QUERY_KEY = 3
    URL_QUERY_VALUE = 4
    URL_PROTOCOL = 5
    URL_PARSING_SYMBOL = 6
    UNDEFINED = 7
    MULTI_URL_CONTAINER=8

class EncodeUrlRankTreeResult():
    def __init__(self, rankTree, url:str, regexPattern:str) -> None:
        self._tree = rankTree
        self._url = url
        self._re = regexPattern

    def getRankTree(self):
        return self._tree
    
    def getUrl(self):
        return self._url

    def getRegex(self):
        return self._re

class TextRegexPair():
    def __init__(self,text:str,regexPatrn:str) -> None:
        self.text = text
        self.regexPatrn = regexPatrn


class ParsedUrl():
    def __init__(self) -> None:
        self._domain = ''
        self._paths: list[TextRegexPair] = []
        self._queries: list[tuple[TextRegexPair,TextRegexPair]] = []
    
    def getDomain(self):
        return self._domain
    def setDomain(self, domain):
        self._domain = domain
    domain = property(getDomain,setDomain)
    
    def getPaths(self):
        return self._paths
    def addPath(self, path:str, pathRegexPatrn:str):
        self._paths.append(TextRegexPair(path,pathRegexPatrn))
    paths:list[TextRegexPair] = property(getPaths)
    
    def getQueries(self):
        return self._queries
    def addQuery(self, query:tuple, queryRegexPatrn:tuple):
        self._queries.append((TextRegexPair(query[0],queryRegexPatrn[0]),TextRegexPair(query[1],queryRegexPatrn[1])))
    queries:list[tuple[TextRegexPair,TextRegexPair]] = property(getQueries)


class ParsedUrlParser():

    def __init__(self, url:str) -> None:
        self._url = url
        self._fullUrl = f'{url}'
        self._parsedUrl = ParsedUrl()

    captureUrlComponents = False
    requireUrlProtocol = True
    reNoCapt = '' if captureUrlComponents else '?:'
    reCondProtcl = '' if requireUrlProtocol else '?'

    #TODO: Use one big regex with named captures for each part of the url, then for match.groupDict()['paths'] say, run the path_match regex below on a find_iter style

    URL_DOMAIN_MATCH = r'^(({0}({0}http[s]?|ftp):\/\/){1}({0}[^:\/\s]+))'.format(reNoCapt, reCondProtcl)

    URL_PATH_MATCH = r'^(({0}\/[\w.\-_]+))'.format(reNoCapt)

    URL_QUERY_FLAG_MATCH = r'^\?|\/\?'
    
    URL_QUERY_KEY_MATCH = r'^(?:&)?([^\=\&]+)'
    URL_QUERY_VALUE_MATCH = r'^(?:=)([^\=\&]+)'

    def getParsedUrl(self):
        return self._parsedUrl

    parsedUrl:ParsedUrl = property(getParsedUrl)

    def _parseUrlDomain(self):
        assert not self._parsedUrl.domain, f'Domain already set as: {self._parsedUrl.domain}'
        _matches = re.findall(ParsedUrlParser.URL_DOMAIN_MATCH, self._url)
        if _matches:
            assert self._url.index(self._parsedUrl.domain) == 0, 'Domain must be located at index 0'
            self._parsedUrl.domain = _matches[0]
            self._url = self._url[len(self._parsedUrl.domain):]
        assert self._parsedUrl.domain, f'No domain set for url: {self._url}'
        
        return self

    
    def _parseUrlPaths(self):
        assert self._parsedUrl, 'Parsing Url Paths requires a ParsedUrls object'
        assert self._parsedUrl.domain, 'Parsing Url Paths requires the domain to be set on the ParsedUrls object'
        _matches = re.findall(ParsedUrlParser.URL_PATH_MATCH, self._url)
        _i = 0
        while _matches and _i < 30:
            _i += 1
            m = re.sub(r'^\/', '', _matches[0])
            assert self._url.index(_matches[0]) == 0, f'Next Path ({_matches[0]}) must be located at index 0: ({self._url})'
            self._parsedUrl.addPath(m, ParsedUrlParser.URL_PATH_MATCH)
            self._url = self._url[len(_matches[0]):]
            _matches = re.findall(ParsedUrlParser.URL_PATH_MATCH, self._url)

        return self

    def _parseUrlCheckForQueryFlag(self):
        result = bool(re.match(ParsedUrlParser.URL_QUERY_FLAG_MATCH, self._url))
        if result:
            self._url = re.sub(r'^\?','', self._url)
        return result

    def _parseUrlQueries(self):
        assert self._parsedUrl, 'Parsing Url Paths requires a ParsedUrls object'
        assert self._parsedUrl.domain, 'Parsing Url Paths requires the domain to be set on the ParsedUrls object'
        
        _qkMatches = re.findall(ParsedUrlParser.URL_QUERY_KEY_MATCH, self._url)
        _i = 0
        while _qkMatches and _i < 30:
            _i += 1
            self._url = re.sub(r'^&','', self._url)
            assert self._url.index(_qkMatches[0]) == 0, 'Next Path must be located at index 0'
            self._url = self._url[len(_qkMatches[0]):]
            _qvMatches = re.findall(ParsedUrlParser.URL_QUERY_VALUE_MATCH, self._url)
            if _qvMatches:
                self._parsedUrl.addQuery((_qkMatches[0],_qvMatches[0]), (ParsedUrlParser.URL_QUERY_KEY_MATCH, ParsedUrlParser.URL_QUERY_VALUE_MATCH))
                self._url = re.sub(r'^=','', self._url)
                self._url = self._url[len(_qvMatches[0]):]
            else:
                self._parsedUrl.addQuery((_qkMatches[0],''), (ParsedUrlParser.URL_QUERY_KEY_MATCH, ''))
            _qkMatches = re.findall(ParsedUrlParser.URL_QUERY_KEY_MATCH, self._url)

        return self

    def parseUrl(self):
        (self
         ._parseUrlDomain()
         ._parseUrlPaths())
        if self._parseUrlCheckForQueryFlag():
            self._parseUrlQueries()
        return self
