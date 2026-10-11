#!/bin/sh
# Builds small tagged documents with pdfLaTeX and LuaLaTeX, then checks them
# with veraPDF's PDF/UA-2 profile. Needs Docker. After the two image pulls,
# the containers run with networking off. Each file is compiled at least twice,
# then again while the log asks for a rerun (at most 5 times). hyperref.tex is
# also built under pdfLaTeX with exactly 2 passes, in pdflatex-2pass/.
#   ./check.sh       4 files x 2 engines, about two minutes
#   ./check.sh all   also 40 single packages and 6 classes under pdfLaTeX
set -eu
TL=texlive/texlive@sha256:a7ae4dfa9d521b5db14446872fa488b839021d1f604d0a3c74461784895f2a67
VP=verapdf/cli@sha256:d565095c67a083e693aebf7d1a15784007370571053fc1aa5b502665b9a78f9c
DM='\DocumentMetadata{lang=en, pdfversion=2.0, pdfstandard=ua-2, tagging=on}'
PKGS='amsmath amssymb graphicx hyperref booktabs xcolor amsthm mathtools geometry
fontenc amsfonts enumitem inputenc microtype multirow url subcaption array tikz
algorithm float natbib cleveref algpseudocode mathrsfs caption times bm lmodern
placeins tabularx bbm babel color longtable tcolorbox comment cite authblk dsfont'
CLASSES='amsart IEEEtran acmart elsarticle llncs revtex4-2'
mkdir -p cases && cd cases

doc() {  # $1 = class, $2 = extra preamble line
  printf '%s\n\\documentclass{%s}\n%s\n' "$DM" "$1" "$2"
  cat <<'TEX'
\title{Test document}
\author{A. Author}
\date{}
\begin{document}
\maketitle
\section{Introduction}
Text with inline math $a^2+b^2=c^2$.
\begin{equation}
\int_0^1 x^2\,dx = \frac{1}{3} \label{eq:a}
\end{equation}
See equation~\ref{eq:a} and Table~\ref{tab:a}.
\[ \sum_{k=1}^{n} k = \frac{n(n+1)}{2} \]
\subsection{List}
\begin{itemize}
\item One
\item Two
\end{itemize}
\begin{table}[h]
\centering
\caption{A table}\label{tab:a}
\begin{tabular}{lr}
Name & Value\\
x & 1
\end{tabular}
\end{table}
\section{Conclusion}
Done.
\end{document}
TEX
}
footnote() {  # $1 = extra preamble line
  printf '%s\n\\documentclass{article}\n%s\n' "$DM" "$1"
  printf '%s\n' '\title{Footnote test}\date{}' '\begin{document}' '\maketitle' \
    'Text with a footnote\footnote{A note.}.' '\end{document}'
}
doc article ''                          > plain.tex
doc article '\usepackage{hyperref}'     > hyperref.tex
footnote ''                             > footnote.tex
footnote '\renewcommand\footnoterule{}' > footnote-norule.tex
both='plain hyperref footnote footnote-norule'; single=''
if [ "${1:-}" = all ]; then
  for p in $PKGS; do doc article "\\usepackage{$p}" > "pkg-$p.tex"; single="$single pkg-$p"; done
  for c in $CLASSES; do doc "$c" '' > "cls-$c.tex"; single="$single cls-$c"; done
fi

docker pull -q "$TL" >/dev/null && docker pull -q "$VP" >/dev/null
U="--user $(id -u):$(id -g) -e HOME=/tmp"
docker run --rm --network none $U -v "$PWD":/w -w /w "$TL" sh -c '
  RR="Rerun to get|Label\(s\) may have changed|Warning:.*[Rr]erun|[Pp]lease rerun"
  run() {  # $1 = engine, $2 = file, $3 = output directory, $4 = fixed pass count (optional)
    mkdir -p $3; n=0
    while [ $n -lt 5 ]; do n=$((n+1))
      $1 -interaction=nonstopmode -output-directory=$3 $2.tex >/dev/null 2>&1 || true
      if [ -n "$4" ]; then [ $n -ge $4 ] && break
      elif [ $n -ge 2 ] && ! grep -Eq "$RR" $3/$2.log; then break; fi
    done; echo "$3/$2: $n passes"; }
  for f in '"$both"'; do run pdflatex $f pdflatex; run lualatex $f lualatex; done
  run pdflatex hyperref pdflatex-2pass 2
  for f in '"$single"'; do run pdflatex $f pdflatex; done'
docker run --rm --network none $U -v "$PWD":/w:ro --entrypoint sh "$VP" -c \
  '/opt/verapdf/verapdf -f ua2 --format text /w/pdflatex-2pass/*.pdf /w/pdflatex/*.pdf /w/lualatex/*.pdf' 2>/dev/null \
  | sed 's#/w/##' || true
