# ML surrogates for the DFT stage

The brief's §14 stage A asks for Ag–Cu mixing energies. Doing that with VASP
needs a licence, an HPC allocation and roughly 730 core-hours. A universal
machine-learned interatomic potential does the same calculation on a laptop in
minutes.

This document is about when that substitution is legitimate and when it is not.

---

## 1. What these models are — and what they are not

**They are not language models.** An LLM cannot compute a formation energy. The
relevant class is a **machine-learned interatomic potential**: a graph neural
network over atomic positions, with rotational and translational equivariance
built into the architecture, trained on large DFT datasets to predict energy
and forces directly from structure.

| Model | Package | Notes |
|---|---|---|
| **MACE-MP-0** | `mace-torch` | Strongest general accuracy; ~100 MB; runs on CPU |
| **CHGNet** | `chgnet` | Smaller and faster; also predicts magnetic moments |
| **M3GNet** | `matgl` | The original MP universal potential |
| **SevenNet** | `sevenn` | Strong on metals; GPU-oriented |

**They are trained on the Materials Project** — the same database
`pvdlowe.mp` queries. That is convenient, because it means the framework
already holds reference values to test them against.

## 2. Why validation is mandatory here

Reported held-out errors are of order 30–50 meV/atom. The Ag–Cu mixing
energies this project cares about are of order 50–100 meV/atom. **The error bar
is comparable with the signal.**

Worse, the training distribution is dominated by ordered stoichiometric
crystals near the convex hull. Every structure this project needs — a
disordered sputtered solid solution, a 1 at.% dilute ternary, a metal/oxide
interface — sits in a sparse region of that distribution, where the reported
errors do not apply.

So `pvdlowe surrogate` validates before it computes:

```bash
python -m pvdlowe surrogate --validate
```

Cu₃Ag and CuAg₃ are the only ordered Ag–Cu phases in the Materials Project, and
the framework recorded their energies above hull during stage 2 — **0.0904 and
0.0857 eV/atom**. Those are free reference points. If a surrogate cannot
reproduce them, nothing it says about a disordered alloy of the same two
elements should be believed.

Passing at 50 meV/atom means the model is behaving as advertised. It does not
mean it is accurate enough for a thermodynamic conclusion on its own.

## 3. Provenance

Surrogate results are graded **`ML_SURROGATE`**, ranked **below** `DFT_OWN` and
`MP_API`, and flagged `needs_verification`. `assert_reportable` therefore blocks
them from headline tables.

This is deliberate and it is the brief's own §12 position — *do not put
numerical DFT values into a thesis as if they were established facts* — applied
to a tool the brief did not anticipate. A surrogate tells you **which
calculations are worth running**. It does not replace running them.

## 4. What to run

```bash
pip install mace-torch ase          # ~100 MB, CPU-capable
python -m pvdlowe surrogate                     # list models, check install
python -m pvdlowe surrogate --validate          # MUST pass before trusting output
python -m pvdlowe surrogate -o results/surrogate_agcu.csv
python -m pvdlowe surrogate --ternaries         # the brief's dilute Ti and Al
```

The Ag–Cu series over a 32-site cell takes a few minutes on CPU.

## 5. What each result would mean

**Mixing energies.** The Materials Project already established that Ag–Cu has no
stable ordered compound, with the nearest phases 86–90 meV/atom above the hull —
so the equilibrium answer is known. What the surrogate adds is the shape of the
curve for *disordered* compositions, which the database does not contain. If the
surrogate gives ΔE_mix well above k_BT at deposition (26 meV at 300 K, 48 meV at
550 K) across the series, that reinforces §3.7's segregation conclusion and
predicts the direction of the annealing experiment.

**Ternaries.** This is the weakest application in the module, and the one to be
most careful with. A single substituted atom in a 108-site cell is a dilute
limit these models are not specifically trained for. The question it can answer
is directional only — does the addition raise or lower the mixing energy? Note
that §3.7 already found 8 near-hull Cu–Ti phases and 10 Al–Cu phases, so on
annealing a dilute addition has intermetallics available to precipitate rather
than remaining in solution as a stabiliser. A surrogate result that contradicts
that should be distrusted before the database is.

## 6. What a surrogate cannot do for this project

- **Interface energies (stage B).** Possible in principle, but AZO/metal
  interfaces are far outside the training distribution and would need their own
  validation, which there is nothing to validate against.
- **Optical constants.** These models predict energies and forces, not
  dielectric functions. The framework's optical layer is unaffected.
- **Anything about the sputtered microstructure.** The two open questions in
  this project — copper's grain structure and the Ag–Cu microstructure — are
  kinetic, not thermodynamic. No energy model answers them; the XRD scan does.

## 7. Honest summary

A surrogate makes stage A cheap enough to be worth doing, and validates itself
against values the project already holds. It does not make stage A a *result*,
and it does not touch the two measurements that actually gate this project.

If the choice is between an afternoon on the surrogate and an afternoon on the
XRD scan, **take the XRD**.
