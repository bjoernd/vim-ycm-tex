#!/usr/bin/env python

import vim
import re
import subprocess
import shlex
import glob

from ycm.completers.threaded_completer import ThreadedCompleter

class LatexCompleter( ThreadedCompleter ):
    """
    Completer for LaTeX that takes into account BibTex entries
    for completion.
    """

    # LaTeX query types we are going to see
    # TODO: make this an enum
    NONE      = 0
    CITATIONS = 1
    LABELS    = 2

    def __init__( self ):
        self.complete_target = self.NONE
        super( LatexCompleter, self ).__init__()


    def ShouldUseNowInner( self, start_col ):
        """
        Used by YCM to determine if we want to be called for the
        current buffer state.
        """

        # we only want to be called for \cite{} and \ref{} completions,
        # otherwise the default completer will be just fine
        if (vim.current.line[start_col-1:start_col+5] == r'\cite{') or \
           (vim.current.line[start_col-1:start_col+4] == r'\ref{')  or \
           (vim.current.line[start_col-1:start_col+5] == r'\vref{'):
            return True

        return super( LatexCompleter, self ).ShouldUseNowInner( start_col )


    def SupportedFiletypes( self ):
        """
        Determines which vim filetypes we support
        """
        return ['plaintex', 'tex']


    def CandidatesForQueryAsyncInner(self, query, start_col):
        """
        This function triggers a query for completion
        candidates.
        """
        #f = file("log", "a")
        data = vim.current.line

        #f.write("CandidatesForQueryAsyncInner: q %s col %d\n" % (query, start_col))

        # Check if we are completing either a \cite{} or a \ref{}. If so,
        # set the completion target type.
        if data[start_col-5:start_col-1] == "cite":
            self.complete_target = self.CITATIONS
        elif data[start_col-4:start_col-1] == "ref" or \
             data[start_col-5:start_col-1] == "vref":
            self.complete_target = self.LABELS

        super(LatexCompleter, self).CandidatesForQueryAsyncInner(query, start_col)


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
            ret.append(re.sub(r"@(.*){([^,]*).*", r"\2", l))
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
            ret.append(re.sub(r".*\label{(.*)}.*", r"\1", label))

        return ret


    def ComputeCandidates( self, query, col ):
        """
        Worker function executed by the asynchronous
        completion thread.
        """
        if self.complete_target == self.LABELS:
            return self._FindLabels()
        if self.complete_target == self.CITATIONS:
            return self._FindBibEntries()

        self.complete_target = self.NONE

        return self._FindLabels() + self._FindBibEntries()
