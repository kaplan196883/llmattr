"""Round-30 math-explanation fixes per GPT-5.5 audit."""
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
text = ARTICLE.read_text(encoding="utf-8")
original_len = len(text)

# === FAIL #1: define d in C2 ===
# Line 454-461: \(d \ge 0.5\) appears with d undefined inline.
# Change to: "Cohen's \(d \ge 0.5\)" so the effect-size meaning is explicit
# (the surrounding §4.7 already defines Cohen's d for recursive-vs-baseline).
text = text.replace(
    "\\ge 2\n\\quad\n\\text{and}\n\\quad\nd\\ge 0.5.",
    "\\ge 2\n\\quad\n\\text{and}\n\\quad\n\\text{Cohen's } d\\ge 0.5.",
)

# === FAIL #2: V symbol collision in §4.9 ===
# Line 947: empirical vector field \(v(x)=(U(x),V(x))\) uses V as y-component.
# Line 952: effective potential \[V(x)=-\log(\hat\rho(x)+\epsilon)\] uses V as scalar potential.
# Same letter for different objects. Rename vector-field components to (u, w)
# so the potential V is unambiguous.
text = text.replace(
    "\\(v(x)=(U(x),V(x))\\) that represents the average",
    "\\(v(x)=(u(x),w(x))\\) that represents the average",
)
text = text.replace(
    "\\nabla\\cdot v(x)=\\frac{\\partial U}{\\partial x}+\\frac{\\partial V}{\\partial y}.",
    "\\nabla\\cdot v(x)=\\frac{\\partial u}{\\partial x}+\\frac{\\partial w}{\\partial y}.",
)

# === MINOR fixes ===

# D02 / D24: define \Vert as concatenation on first use in §3.1
# First introduction of \Vert is in line ~333 inside \mathcal{N}_append
# Add an inline definition after the first display block.
text = text.replace(
    "where \\(r_t\\) is the role label assigned to the turn and alternates according to the dialog protocol.",
    "where \\(\\Vert\\) denotes string concatenation, \\(r_t\\) is the role label assigned to the turn (alternating "
    "according to the dialog protocol), and \\(\\operatorname{format\\_turn}(r_t,Y_t)\\) is the role-labeled "
    "rendering of the model output that is appended to the prior context.",
)

# D15: define \lambda_{1,r}^{late} inline at C4 introduction
text = text.replace(
    "**C4. Re-entry, contraction, or absorbing collapse.** The regime passes if at least one of the following holds:",
    "**C4. Re-entry, contraction, or absorbing collapse.** Let \\(\\lambda_{1,r}^{\\mathrm{late}}\\) be the top "
    "finite-time ensemble-spread exponent for regime \\(r\\) computed in the late window (defined in §4.5.2), "
    "let \\(R_r\\) and \\(SD_r\\) denote regime-mean recurrence and sharpness dimension, and let "
    "\\(\\texttt{best\\_period}\\) and \\(\\texttt{period\\_2\\_score}\\) denote the periodicity diagnostics "
    "from §4.5.1. The regime passes if at least one of the following holds:",
)

# D28: expand N_families etc. inline
text = text.replace(
    "trajectories. Publication-scale defaults differ by experiment family:",
    "trajectories, where \\(N_{\\text{families}}\\) is the number of distinct prompt families, "
    "\\(N_{\\text{ICs}}\\) is the number of initial conditions per family, and "
    "\\(N_{\\text{runs}}\\) is the number of independent runs per (family, IC) cell. "
    "Publication-scale defaults differ by experiment family:",
)

# D35: clarify the algorithmic persist event matches the strict
# post-injection-cluster definition; relate to S_persist estimand
text = text.replace(
    "6. Define persistent escape:\n   \\[\n   \\operatorname{persist}=\\operatorname{jump}\\wedge\n   \\left[C(O(Z_T))=C(O(Z_{t_{\\mathrm{inj}}+1}))\\right]\n   \\]",
    "6. Define persistent escape (the strict variant: trajectory remains in the *post-injection* cluster, not "
    "merely in any cluster other than the reference):\n   \\[\n   \\operatorname{persist}=\\operatorname{jump}\\wedge\n   "
    "\\left[C(O(Z_T))=C(O(Z_{t_{\\mathrm{inj}}+1}))\\right]\n   \\]",
)

# D46: define epsilon as small stabilizer
text = text.replace(
    "V(x)=-\\log(\\hat\\rho(x)+\\epsilon).\n\\]",
    "V(x)=-\\log(\\hat\\rho(x)+\\epsilon),\n\\]\n\nwhere \\(\\epsilon>0\\) is a small numerical stabilizer "
    "preventing log of zero in low-density grid cells.",
)

# Also need to update the dialog rule in §4.1 (line ~635) to include clip
# for consistency with §3.1's clipped form.
text = text.replace(
    "\\text{Dialog:}\\quad X_{t+1}=\\mathcal{N}_{\\text{dialog}}(X_t,Y_t)=X_t\\Vert \\operatorname{format\\_turn}(r_t,Y_t)",
    "\\text{Dialog:}\\quad X_{t+1}=\\mathcal{N}_{\\text{dialog}}(X_t,Y_t)=\\operatorname{clip}\\!\\left(X_t\\Vert \\operatorname{format\\_turn}(r_t,Y_t)\\right)",
)

ARTICLE.write_text(text, encoding="utf-8")
print(f"applied {original_len - len(text):+d} char delta (length now {len(text)})")

# Verify the FAILs are gone
import re
if "d\\ge 0.5" in text and "Cohen's } d" not in text:
    print("WARN: D13 fix may not have applied")
else:
    print("D13 (Cohen's d): fixed")
if "(U(x),V(x))" in text:
    print("WARN: D47 fix incomplete")
else:
    print("D47 (V collision): fixed")
