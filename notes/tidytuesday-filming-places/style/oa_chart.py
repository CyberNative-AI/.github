"""CyberNative charts for matplotlib.

    import sys; sys.path.insert(0, "<kit>")     
    import oa_chart
    pal = oa_chart.use()            # or oa_chart.use("ground") for a chart on the graphite field
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.barh(names, values)
    oa_chart.values(ax, bars, over=0.9)  # value at each bar's end, DM Mono; over the limit = rust
    oa_chart.limit(ax, 0.9, "Budget")   # rust marks a limit; it is never a series colour
    oa_chart.legend(ax)             # several series only: one row above the plot, no box
    oa_chart.finish(ax, title="…", source="…")  # mono figures; title and source share the plot's left edge

One measure is one colour: colour bars by series, never by category. The sheet has four series,
the graphite field three (a fourth would fall under 3:1 against graphite); past that, split the chart.

use() registers the kit's TTFs (fonts/ttf/), loads cybernative.mplstyle and returns the palette
for the surface. Values come from tokens.json; nothing here invents a colour.
"""
import glob
import json
import os

KIT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(KIT, "tokens.json"), encoding="utf-8") as _fh:
    TOKENS = json.load(_fh)
_STATE = {"surface": "sheet"}


def use(surface="sheet"):
    """Register the faces, apply the style and return the palette for 'sheet' or 'ground'."""
    import matplotlib as mpl
    from matplotlib import font_manager

    for path in sorted(glob.glob(os.path.join(KIT, "fonts", "ttf", "*.ttf"))):
        font_manager.fontManager.addfont(path)
    mpl.style.use(os.path.join(KIT, "cybernative.mplstyle"))
    pal = TOKENS["chart"][surface]
    if surface == "ground":
        mpl.rcParams.update({
            "figure.facecolor": pal["background"], "axes.facecolor": pal["background"],
            "savefig.facecolor": pal["background"], "axes.edgecolor": pal["text"],
            "axes.labelcolor": pal["label"], "axes.titlecolor": pal["text"], "text.color": pal["text"],
            "xtick.color": pal["label"], "ytick.color": pal["label"],
            "xtick.labelcolor": pal["label"], "ytick.labelcolor": pal["label"],
            "grid.color": pal["grid"], "patch.edgecolor": pal["background"],
            "axes.prop_cycle": mpl.cycler(color=pal["series"]),
        })
    _STATE["surface"] = surface
    return pal


def _pal():
    return TOKENS["chart"][_STATE["surface"]]


def values(ax, bars, fmt="{:g}", inside=False, over=None):
    """Write each bar's value at its end in DM Mono (outside the bar unless inside=True).

    over: a limit; values above it are written in rust, as in the HTML kit."""
    pal = _pal()
    horizontal = getattr(bars, "orientation", "vertical") == "horizontal"
    for bar in bars:
        if horizontal:
            v = bar.get_width()
            ax.annotate(fmt.format(v), (bar.get_x() + v, bar.get_y() + bar.get_height() / 2),
                        xytext=(-8 if inside else 8, 0), textcoords="offset points",
                        ha="right" if inside else "left", va="center", family="monospace",
                        fontsize=10, fontweight=500,
                        color=pal["limit"] if over is not None and v > over else pal["text"])
        else:
            v = bar.get_height()
            ax.annotate(fmt.format(v), (bar.get_x() + bar.get_width() / 2, bar.get_y() + v),
                        xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                        family="monospace", fontsize=10, fontweight=500,
                        color=pal["limit"] if over is not None and v > over else pal["text"])


def limit(ax, at, label, axis="x"):
    """A limit line in rust with its label in mono: the only use of rust in a chart."""
    rust = _pal()["limit"]
    line = ax.axvline if axis == "x" else ax.axhline
    line(at, color=rust, linewidth=1.6, linestyle=(0, (4, 3)), zorder=3)
    if axis == "x":
        # the label sits above the plot, so it never lands on a bar
        ax.annotate(label.upper(), (at, 1), xycoords=("data", "axes fraction"), xytext=(0, 6),
                    textcoords="offset points", ha="center", va="bottom", family="monospace",
                    fontsize=9, fontweight=500, color=rust)
    else:
        ax.annotate(label.upper(), (0, at), xycoords=("axes fraction", "data"), xytext=(6, 4),
                    textcoords="offset points", ha="left", va="bottom", family="monospace",
                    fontsize=9, fontweight=500, color=rust)


def legend(ax, **kw):
    """One row of series keys above the plot, under the title, with no box."""
    handles, labels = ax.get_legend_handles_labels()
    opts = dict(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=len(labels), frameon=False,
                borderaxespad=0.4, handlelength=1.6, columnspacing=1.6, fontsize=10)
    opts.update(kw)
    return ax.legend(handles, labels, **opts)


def finish(ax, title=None, source=None):
    """Mono figures on value axes (category names stay in DM Sans), left title, source line."""
    from matplotlib.category import StrCategoryFormatter
    for axis, name in ((ax.xaxis, "x"), (ax.yaxis, "y")):
        if not isinstance(axis.get_major_formatter(), StrCategoryFormatter):
            ax.tick_params(axis=name, labelfontfamily="monospace")
    if title:
        ax.set_title(title, loc="left", family="sans-serif", fontweight=600)
    if source:
        # on the plot's left edge, like the title; never flush with the image edge
        ax.annotate(source, (0, 0), xycoords=("axes fraction", "figure fraction"), xytext=(0, 8),
                    textcoords="offset points", ha="left", va="bottom", fontsize=9,
                    color=_pal()["label"])
