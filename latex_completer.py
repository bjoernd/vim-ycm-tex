#!/usr/bin/env python

import re
import subprocess
import shlex
import glob
import logging

from ycm.completers.completer import Completer
from ycm.server import responses

LOG = logging.getLogger(__name__)

class LatexCompleter( Completer ):
    """
    Completer for LaTeX that takes into account BibTex entries
    for completion.
    """

    # LaTeX query types we are going to see
    # TODO: make this an enum
    NONE      = 0
    CITATIONS = 1
    LABELS    = 2

    def __init__( self, user_options ):
        super( LatexCompleter, self ).__init__( user_options )
        self.complete_target = self.NONE


    def DebugInfo( self, request_data ):
        return "TeX completer %d" % self.complete_target


    def ShouldUseNowInner( self, request_data ):
        """
        Used by YCM to determine if we want to be called for the
        current buffer state.
        """

        # we only want to be called for \cite{} and \ref{} completions,
        # otherwise the default completer will be just fine

        line = request_data["line_value"]
        col  = request_data["start_column"]
        LOG.debug('"%s"' % line)
        LOG.debug("'%s'" % line[col-5:col])

        if (line[col-6:col] == r'\cite{'):
            self.complete_target = self.CITATIONS
            LOG.debug("complete target %d" % self.complete_target)
            return True

        if (line[col-5:col] == r'\ref{')  or \
           (line[col-6:col] == r'\vref{'):
            self.complete_target = self.LABELS
            LOG.debug("complete target %d" % self.complete_target)
            return True

        return super( LatexCompleter, self ).ShouldUseNowInner( request_data )


    def SupportedFiletypes( self ):
        """
        Determines which vim filetypes we support
        """
        return ['plaintex', 'tex']


    def _FindBibFiles(self, texfile):
        """
        Parse the given tex file (name) to find the bib files included.
        """
        biblist = []
        # TODO This regex is not very robust.  Which characters my apear in
        # bib filenames?  Doesn't \bibliography{} accept a comma seperated
        # list?
        regex = re.compile(r'^[^%]*\\bibliography\s*{(.*)}.*$')
        for line in open(texfile):
            match = regex.search(line)
            if match != None:
                biblist.append(match.group(1) + '.bib')

        # If no bib files where found in the tex file use the bib files in the
        # current directory.
        if biblist == []:
            biblist.append(glob.glob("*.bib"))

        return biblist


    def _FindBibEntries(self):
        """
        Find BIBtex entries.

        I'm currently assuming, that Bib entries have the format
        ^@<articletype> {<ID>,
            <bibtex properties>
            [..]
        }

        Hence, to find IDs for completion, I scan for lines starting
        with an @ character and extract the ID from there.

        The search is done by a shell pipe:
            cat *.bib | grep ^@ | grep -v @string
        """
        bibs = " ".join(glob.glob("*.bib"))
        cat_process  = subprocess.Popen(shlex.split("cat %s" % bibs),
                                        stdout=subprocess.PIPE)
        grep_process = subprocess.Popen(shlex.split("grep ^@"),
                                        stdin=cat_process.stdout,
                                        stdout=subprocess.PIPE)
        cat_process.stdout.close()
        grep2_process = subprocess.Popen(shlex.split("grep -vi @string"),
                                         stdin=grep_process.stdout,
                                         stdout=subprocess.PIPE)
        grep_process.stdout.close()

        lines = grep2_process.communicate()[0]

        ret = []
        for l in lines.split("\n"):
            ret.append(responses.BuildCompletionData(
                    re.sub(r"@([A-Za-z]*)\s*{\s*([^,]*),.*", r"\2", l)
                )
            )
        return ret


    def _FindLabels(self):
        """
        Find LaTeX labels for \ref{} completion.

        This time we scan through all .tex files in the current
        directory and extract the content of all \label{} commands
        as sources for completion.
        """
        texs = " ".join(glob.glob("*.tex"))
        cat_process  = subprocess.Popen(shlex.split("cat %s" % texs),
                                        stdout=subprocess.PIPE)
        grep_process = subprocess.Popen(shlex.split(r"grep \\\\label"),
                                        stdin=cat_process.stdout,
                                        stdout=subprocess.PIPE)
        cat_process.stdout.close()

        lines = grep_process.communicate()[0]

        ret = []
        for label in lines.split("\n"):
            ret.append(responses.BuildCompletionData(
                    re.sub(r".*\label{(.*)}.*", r"\1", label)
                )
            )

        return ret


    def ComputeCandidatesInner( self, request_data ):
        """
        Worker function executed by the asynchronous
        completion thread.
        """
        LOG.debug("compute candidates %d" % self.complete_target)
        if self.complete_target == self.LABELS:
            return self._FindLabels()
        if self.complete_target == self.CITATIONS:
            return self._FindBibEntries()

        self.complete_target = self.NONE

        return self._FindLabels() + self._FindBibEntries()
