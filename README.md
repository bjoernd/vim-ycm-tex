vim-ycm-tex
===========


What is this?
-------------

This is a Latex Completer for [YouCompleteMe](https://github.com/Valloric/YouCompleteMe).
It completes citations (`\cite{}`) and references to labels (`\ref{}`).

How do I use it?
----------------

* YCM completers need to be made available in your YCM directory. There's a
  subdirectory `python/ycm/completers`.  This completer should be added there
  with the name `tex`.

* To enable automatic completion, you need to tell YCM about the triggers that
  should run the TeX completer. These triggers are LaTeX's \ref and \cite comannds.
  YCM provides the `g:ycm_semantic_triggers` option that allows adding new triggers.
  Therefore, add
  
  ```vim
  let g:ycm_semantic_triggers = {
  \  'tex'  : ['\ref{','\cite{'],
  \ }
  ```

  to your `.vimrc` to enable automatic semantic completion. *(Found by Bart Z. Yueshen)*
  

Are there limitations?
----------------------

Of course:

* The completer uses hard-coded Linux shell commands and therefore won't work
  on Windows.

* The BIB completion only considers BIB files in the current working directory.

* BIB entries are assumed to start at the beginning of a line and have the format:
  `\<type>{<name>, ...` -- `name` will then be selected for completion.
