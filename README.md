# jpc-style

This is the LaTeX style for the Journal of Privacy and Confidentiality. Submission instructions are available at https://journalprivacyconfidentiality.org/index.php/jpc/about/submissions. 

## Source
The style is derived from LMCS style at https://lmcs.episciences.org/page/authors-latex-style .

## On Overleaf

This can be found on Overleaf: https://v2.overleaf.com/read/jcvxjtfqvgyz

## Implementing

## For final Layout

Add the following lines after the `\documentclass` lines:

```
% JPC Layouting Macros
% THESE ARE ADDED BY THE EDITORIAL TEAM - NO NEED TO SET HERE
\newcommand{\doisuffix}{v0.i0.999}
% \jpcheading{vol}{issue}{year}{notused}{subm}{publ}{rev}{spec_iss}{title}
\jpcheading{0}{0}{2000}{}{Mar.~20, 2017}{Jun.~22, 2018}{}{Special issue}
```

