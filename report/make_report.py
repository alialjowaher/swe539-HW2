#!/usr/bin/env python3
r"""Build the figures and generated LaTeX for the HW2 LLM-refactoring report.

Reads every run in ../refactor-kit/runs (run.json, metrics.json, tests_*.json) and writes
  figures/fig_changes.pdf    lines changed + target-method complexity
  figures/fig_cohesion.pdf   reported mean LCOM* vs. pre-existing classes
  generated/numbers.tex      every number the prose uses, read with \val{key}
  generated/smells.tex       the smell / technique table
  generated/results.tex      the 12-run results table
Copilot's runs were logged under three LLM names (Copilot, Copilot-W01, Copilot-B01);
they are merged here into one family by the part before the first '-'.

Run with a Python that has matplotlib:  ~/tools/hw2-venv/bin/python make_report.py
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

HERE = Path(__file__).resolve().parent
KIT = HERE.parent / "refactor-kit"
FIG, GEN = HERE / "figures", HERE / "generated"

SMELLS = ["W01", "W04", "B01", "B02"]
FAMS = ["Claude", "Gemini", "Copilot"]
LABEL = {"Claude": "Claude Opus 5.5", "Gemini": "Gemini 3.1 Pro", "Copilot": "Copilot"}
# dataviz reference palette, categorical slots 1-3 (validated all-pairs, light mode);
# marker shape is the secondary encoding so identity never rests on colour alone.
COLOR = {"Claude": "#2a78d6", "Gemini": "#eb6834", "Copilot": "#1baf7a"}
MARK = {"Claude": "o", "Gemini": "s", "Copilot": "^"}
INK, INK2, GRID, BEFORE = "#0b0b0b", "#52514e", "#e4e3df", "#9a9993"

LOCATION = {  # short location text for the smell table (full text is in TASK.md)
    "W01": r"\texttt{HelpFormatter.appendOptions}",
    "W04": r"\texttt{HelpFormatter.printHelp} (9 parameters)",
    "B01": r"\texttt{HelpFormatter}, \texttt{OptionGroup} $\to$ \texttt{Option}",
    "B02": r"\texttt{Options}, \texttt{DefaultParser}, \texttt{Parser}, \texttt{MissingOptionException}",
}
# target methods shown in Fig. 1b: (smell, class, method/arity, label). Rows whose body moved to
# another member are left out (W04 appendOptions in Copilot's run, B02 updateRequiredOptions).
CC_ROWS = [
    ("W01", "HelpFormatter", "appendOptions/5", "W01  appendOptions"),
    ("W04", "HelpFormatter", "printHelp/9", "W04  printHelp (9 args)"),
    ("B01", "HelpFormatter", "appendOption/3", "B01  appendOption"),
    ("B01", "HelpFormatter", "appendOptions/5", "B01  appendOptions"),
    ("B01", "OptionGroup", "toString/0", "B01  OptionGroup.toString"),
]
COH_CLASSES = [("W04", "HelpFormatter"), ("B01", "Option"), ("B02", "Parser"), ("B02", "DefaultParser")]


def tex(s):
    """Escape plain text for LaTeX (also maps the few non-ASCII symbols the kit uses)."""
    out = []
    for ch in str(s):
        out.append({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
                    "×": r"$\times$", "→": r"$\to$", "–": "--", "—": "---"}.get(ch, ch))
    return "".join(out)


def short(cls):
    return cls.rsplit(".", 1)[-1].replace("$", ".")


def signed(d, nd=0):
    if d is None:
        return "--"
    s = f"{abs(d):.{nd}f}"
    return ("+" if d > 0 else "$-$" if d < 0 else "\\pm") + s if d else "0"


def num(x, nd=0):
    return "--" if x is None else f"{x:.{nd}f}"


def load():
    runs = {}
    for rj in sorted(KIT.glob("runs/*/*/run.json")):
        rd = rj.parent
        r = json.loads(rj.read_text())
        fam = r["llm"].split("-")[0]
        if fam not in FAMS or r["smell"] not in SMELLS:
            continue
        key = (r["smell"], fam)
        if key in runs:
            sys.exit(f"two runs for {key}: {runs[key]['dir']} and {rd}")
        runs[key] = dict(dir=rd, run=r, m=json.loads((rd / "metrics.json").read_text()),
                         to=json.loads((rd / "tests_original.json").read_text()),
                         tr=json.loads((rd / "tests_refactored.json").read_text()))
    missing = [(s, f) for s in SMELLS for f in FAMS if (s, f) not in runs]
    if missing:
        sys.exit(f"missing runs: {missing}")
    return runs


def classes(R):
    return {short(c["class"]): c for c in R["m"]["classes"] if c["counted"]}


def method(R, cls, sig):
    hits = [x for x in R["m"]["methods"] if short(x["class"]) == cls and x["method"].split("[")[0] == sig]
    hits.sort(key=lambda x: x["status"] != "target")
    return hits[0] if hits else None


def build_values(runs):
    V = {}
    base = runs[("W01", "Claude")]
    for R in runs.values():  # every run must share the same baseline
        for k in ("total", "passed", "skipped", "failed", "errors"):
            assert R["to"][k] == base["to"][k], (R["dir"], k)
        assert R["run"]["base_commit"] == base["run"]["base_commit"], R["dir"]
    V["base.commit"] = base["run"]["base_commit"][:7]
    V["tests.total"], V["tests.pass"] = base["to"]["total"], base["to"]["passed"]
    V["tests.skip"], V["tests.fail"] = base["to"]["skipped"], base["to"]["failed"] + base["to"]["errors"]
    V["ck"] = base["m"]["tool"].rsplit(":", 1)[-1]
    V["runs"] = len(runs)
    V["runs.pass"] = sum(R["run"]["verdict"] == "PASS" for R in runs.values())
    V["runs.regr"] = sum(len(R["run"]["regressions"]) for R in runs.values())
    V["runs.att1"] = sum(R["run"]["finish_attempts"] == 1 for R in runs.values())
    for (s, f), R in runs.items():
        p, r = f"{s}.{f}", R["run"]
        V.update({f"{p}.add": r["lines_added"], f"{p}.rem": r["lines_removed"],
                  f"{p}.mchg": r["members"]["changed"], f"{p}.mnew": r["members"]["new"],
                  f"{p}.mrem": r["members"]["removed"], f"{p}.att": r["finish_attempts"],
                  f"{p}.verdict": r["verdict"], f"{p}.regr": len(r["regressions"]),
                  f"{p}.pass": R["tr"]["passed"], f"{p}.total": R["tr"]["total"]})
        for k, name, nd in (("Size", "size", 0), ("Cohesion", "coh", 3), ("Coupling", "cbo", 0)):
            b, a = R["m"]["metrics"][k]["before"], R["m"]["metrics"][k]["after"]
            V[f"{p}.{name}.b"], V[f"{p}.{name}.a"] = num(b, nd), num(a, nd)
            V[f"{p}.{name}.d"] = signed(a - b, nd)
        for cname, c in classes(R).items():
            for met, key, nd in (("loc", "loc", 0), ("wmc", "wmc", 0), ("cbo", "cbo", 0), ("lcom*", "lcom", 3)):
                b, a = (c["before"] or {}).get(met), (c["after"] or {}).get(met)
                V[f"{p}.c.{cname}.{key}.b"], V[f"{p}.c.{cname}.{key}.a"] = num(b, nd), num(a, nd)
                if b is not None and a is not None:
                    V[f"{p}.c.{cname}.{key}.d"] = signed(a - b, nd)
        for x in R["m"]["methods"]:
            sig, cname = x["method"].split("[")[0], short(x["class"])
            for met, key in (("loc", "loc"), ("wmc", "cc")):
                for side, val in (("b", (x["before"] or {}).get(met)), ("a", (x["after"] or {}).get(met))):
                    V.setdefault(f"{p}.m.{cname}.{sig}.{key}.{side}", num(val))
    return V


def write_numbers(V):
    lines = ["% generated by make_report.py from refactor-kit/runs - do not edit by hand"]
    for k in sorted(V):
        lines.append(rf"\expandafter\def\csname val@{k}\endcsname{{{V[k]}}}")
    (GEN / "numbers.tex").write_text("\n".join(lines) + "\n")


def write_smells(runs):
    rows = []
    for s in SMELLS:
        r = runs[(s, "Claude")]["run"]
        typ = "Within" if r["smell_type"].lower().startswith("within") else "Between"
        rows.append(f"{s} & {typ} & {tex(r['smell_name'])} & {LOCATION[s]} & {tex(r['technique'])} \\\\")
    body = "\n".join(rows)
    (GEN / "smells.tex").write_text(
        "\\begin{tabularx}{\\linewidth}{@{}l l l >{\\raggedright\\arraybackslash}X >{\\raggedright\\arraybackslash}p{5.6cm}@{}}\n"
        "\\toprule\nID & Type & Smell & Location & Prescribed refactoring \\\\\n\\midrule\n"
        f"{body}\n\\bottomrule\n\\end{{tabularx}}\n")


def new_types(R):
    out = []
    for c in R["m"]["classes"]:
        if c["counted"] and c["before"] is None and c["after"] is not None:
            n = short(c["class"])
            out.append(f"{n.split('.')[-1]} (nested)" if "." in n else n)
    return ", ".join(out) or "--"


def write_results(runs):
    rows = []
    for gi, s in enumerate(SMELLS):
        if gi:
            rows.append("\\addlinespace[3pt]")
        for i, f in enumerate(FAMS):
            R, r = runs[(s, f)], runs[(s, f)]["run"]
            mt = R["m"]["metrics"]
            sz, co, cb = mt["Size"], mt["Cohesion"], mt["Coupling"]
            assert r["verdict"] == "PASS", (s, f, r["verdict"])  # the caption states that every run passed
            rows.append(" & ".join([
                s if i == 0 else "", f,
                f"{R['tr']['passed']}/{R['tr']['total']}", str(len(r["regressions"])), str(r["finish_attempts"]),
                f"+{r['lines_added']}/$-${r['lines_removed']}",
                f"{r['members']['changed']}/{r['members']['new']}/{r['members']['removed']}",
                tex(new_types(R)),
                f"{sz['before']}$\\to${sz['after']} ({signed(sz['after'] - sz['before'])})",
                f"{co['before']:.3f}$\\to${co['after']:.3f}",
                f"{cb['before']}$\\to${cb['after']}",
            ]) + " \\\\")
    body = "\n".join(rows)
    (GEN / "results.tex").write_text(
        "\\begin{tabular}{@{}l l c c c r c l l l l@{}}\n\\toprule\n"
        "Smell & LLM & Tests & Regr. & Att. & Diff lines & Members & New type & Size & Cohesion & Coupling \\\\\n"
        " & & pass/total & & & +/$-$ & chg/new/rem & & LOC, sum & LCOM*, mean & CBO, sum \\\\\n\\midrule\n"
        f"{body}\n\\bottomrule\n\\end{{tabular}}\n")


# ---------------------------------------------------------------- figures
def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.2, "axes.titlesize": 7.6, "axes.labelsize": 7.2,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "axes.linewidth": 0.6, "xtick.color": INK2,
        "ytick.color": INK2, "xtick.labelcolor": INK, "ytick.labelcolor": INK, "xtick.major.width": 0.6,
        "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 0, "axes.spines.top": False,
        "axes.spines.right": False, "pdf.fonttype": 42, "hatch.linewidth": 0.6, "legend.frameon": False,
        "axes.titlelocation": "left", "axes.titleweight": "bold", "axes.titlecolor": INK,
    })


def tint(hexcol, k=0.55):
    h = hexcol.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(c + (255 - c) * k):02x}" for c in rgb)


def llm_handles():
    return [Line2D([], [], color=COLOR[f], marker=MARK[f], ls="-", lw=1.2, ms=5, label=LABEL[f]) for f in FAMS]


def before_handle():
    return Line2D([], [], color=BEFORE, marker="|", ls="none", ms=9, mew=1.8, label="Before (original code)")


def dumbbell(ax, rows, xlabel, xlim):
    """rows: [(label, before, {fam: after})], drawn top to bottom; one before tick, one dot per LLM."""
    n = len(rows)
    for j, (lab, b, after) in enumerate(rows):
        y = n - 1 - j
        ax.vlines(b, y - 0.36, y + 0.36, color=BEFORE, lw=1.8, zorder=2)
        for i, f in enumerate(FAMS):
            a = after.get(f)
            if a is None:
                continue
            yy = y + (1 - i) * 0.22
            ax.hlines(yy, min(a, b), max(a, b), color=COLOR[f], lw=1.1, alpha=0.75, zorder=2)
            ax.plot(a, yy, marker=MARK[f], ms=5, color=COLOR[f], mec="white", mew=0.6, ls="none", zorder=3)
    ax.set_yticks(range(n), [r[0] for r in rows][::-1])
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)


def fig_changes(runs):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.75, 2.45), gridspec_kw={"width_ratios": [1.0, 1.08]})
    w, gap = 0.24, 0.03
    xs0 = range(len(SMELLS))
    for i, f in enumerate(FAMS):
        xs = [x + (i - 1) * (w + gap) for x in xs0]
        add = [runs[(s, f)]["run"]["lines_added"] for s in SMELLS]
        rem = [runs[(s, f)]["run"]["lines_removed"] for s in SMELLS]
        a1.bar(xs, add, width=w, color=COLOR[f], lw=0, zorder=2)
        a1.bar(xs, [-v for v in rem], width=w, facecolor=tint(COLOR[f]), edgecolor=COLOR[f], hatch="//////",
               lw=0, zorder=2)
    a1.axhline(0, color=INK2, lw=0.7, zorder=3)
    a1.set_xticks(list(xs0), SMELLS)
    a1.tick_params(axis="x", length=0)
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{abs(int(v))}"))
    a1.set_ylabel("Diff lines")
    a1.grid(axis="y", color=GRID, lw=0.6)
    a1.set_axisbelow(True)
    a1.spines["bottom"].set_visible(False)
    lo, hi = a1.get_ylim()
    a1.text(-0.55, hi * 0.92, "added", color=INK2, fontsize=6.6, va="top")
    a1.text(-0.55, lo * 0.92, "removed", color=INK2, fontsize=6.6, va="bottom")
    a1.set_title("(a) Lines added / removed per run")

    rows = []
    for s, cls, sig, lab in CC_ROWS:
        b = method(runs[(s, "Claude")], cls, sig)["before"]["wmc"]
        after = {}
        for f in FAMS:
            mm = method(runs[(s, f)], cls, sig)
            assert mm["before"]["wmc"] == b, (s, f, sig)
            after[f] = (mm["after"] or {}).get("wmc")
        rows.append((lab, b, after))
    dumbbell(a2, rows, "Cyclomatic complexity of the target method (CK)", (0, 21.5))
    a2.set_title("(b) Complexity of the target methods")

    handles = llm_handles() + [before_handle(),
                               Patch(facecolor="#8f8e89", lw=0, label="added"),
                               Patch(facecolor=tint("#8f8e89"), edgecolor="#8f8e89", hatch="//////", lw=0,
                                     label="removed")]
    fig.legend(handles=handles, loc="upper center", ncol=6, fontsize=6.8, handlelength=1.6,
               columnspacing=1.3, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.9), w_pad=2.2)
    fig.savefig(FIG / "fig_changes.pdf")
    plt.close(fig)


def fig_cohesion(runs):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.75, 2.2), sharex=False)
    rows = []
    for s in SMELLS:
        b = runs[(s, "Claude")]["m"]["metrics"]["Cohesion"]["before"]
        rows.append((s, b, {f: runs[(s, f)]["m"]["metrics"]["Cohesion"]["after"] for f in FAMS}))
    xl = "LCOM* (0 = cohesive, 1 = no cohesion; lower is better)"
    dumbbell(a1, rows, xl, (0.4, 1.0))
    a1.set_title("(a) Reported value: mean LCOM* of counted classes")
    rows = []
    for s, cls in COH_CLASSES:
        b = classes(runs[(s, "Claude")])[cls]["before"]["lcom*"]
        rows.append((f"{s}  {cls}", b, {f: classes(runs[(s, f)])[cls]["after"]["lcom*"] for f in FAMS}))
    dumbbell(a2, rows, xl, (0.4, 1.0))
    a2.set_title("(b) Pre-existing classes only")
    fig.legend(handles=llm_handles() + [before_handle()], loc="upper center", ncol=4, fontsize=6.8,
               handlelength=1.6, columnspacing=1.4, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=2.2)
    fig.savefig(FIG / "fig_cohesion.pdf")
    plt.close(fig)


def main():
    FIG.mkdir(exist_ok=True)
    GEN.mkdir(exist_ok=True)
    runs = load()
    V = build_values(runs)
    write_numbers(V)
    write_smells(runs)
    write_results(runs)
    style()
    fig_changes(runs)
    fig_cohesion(runs)
    print(f"{len(runs)} runs -> {len(V)} values, figures in {FIG}, tables in {GEN}")


if __name__ == "__main__":
    main()
