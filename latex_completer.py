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
    
    NONE      = 0
    CITATIONS = 1
    LABELS    = 2
    
    def __init__( self ):
        self.complete_target = self.NONE
        super( LatexCompleter, self ).__init__()
        
        
    def ShouldUseNowInner( self, start_col ):
        if (vim.current.line[start_col-1:start_col+5] == r'\cite{') or \
           (vim.current.line[start_col-1:start_col+4] == r'\ref{'):
            return True
        return super( LatexCompleter, self ).ShouldUseNowInner( start_col )
 

    def SupportedFiletypes( self ):
        return ['plaintex', 'tex']
        

    def CandidatesForQueryAsyncInner(self, query, start_col):
        f = file("log", "a")
        data = vim.current.line
        
        f.write("CandidatesForQueryAsyncInner: q %s col %d\n" % (query, start_col))
        
        if data[start_col-5:start_col-1] == "cite":
            self.complete_target = self.CITATIONS
        elif data[start_col-4:start_col-1] == "ref":
            self.complete_target = self.LABELS
        
        super(LatexCompleter, self).CandidatesForQueryAsyncInner(query, start_col)


    def _FindBibEntries(self):
        bibs = " ".join(glob.glob("*.bib"))
        cat_process  = subprocess.Popen(shlex.split("cat %s" % bibs),
                                        stdout=subprocess.PIPE)
        grep_process = subprocess.Popen(shlex.split("grep ^@"),
                                        stdin=cat_process.stdout,
                                        stdout=subprocess.PIPE)
        cat_process.stdout.close()
        grep2_process = subprocess.Popen(shlex.split("grep -v @string"),
                                         stdin=grep_process.stdout,
                                         stdout=subprocess.PIPE)
        grep_process.stdout.close()
        
        lines = grep2_process.communicate()[0]
        
        ret = []
        for l in lines.split("\n"):
            ret.append(re.sub(r"@(.*){([^,]*).*", r"\2", l))
        return ret
        

    def _FindLabels(self):
        texs = " ".join(glob.glob("*.tex"))
        cat_process  = subprocess.Popen(shlex.split("cat %s" % texs),
                                        stdout=subprocess.PIPE)
        grep_process = subprocess.Popen(shlex.split(r"grep \label"),
                                        stdin=cat_process.stdout,
                                        stdout=subprocess.PIPE)
        cat_process.stdout.close()

        lines = grep_process.communicate()[0]
        
        ret = []
        for label in lines.split("\n"):
            ret.append(re.sub(r".*\label{(.*)}.*", r"\1", label))

        return ret
        

    def ComputeCandidates( self, query, col ):
        if self.complete_target == self.LABELS:
            return self._FindLabels()
        if self.complete_target == self.CITATIONS:
            return self._FindBibEntries()
            
        return self._FindLabels() + self._FindBibEntries()
