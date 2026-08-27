# Script — driving the two interactive views

For the code walkthrough. Two self-contained HTML files, no install, no
network. Open both in browser tabs before the meeting starts.

## The hour

| | Segment | Time | Driven from |
|---|---|---|---|
| 1 | Where the project stands, and what it cannot claim | 5 min | spoken |
| 2 | **The map** — the framework, layer by layer | **25 min** | `project_map.html` |
| 3 | **The review** — ten places worth stopping on | **18 min** | `loc_review.html` |
| 4 | What it found, and the one question for you | 7 min | spoken, or the report |
| 5 | Questions | 5 min | — |

Segment 2 is the bulk, and it is the part your supervisor asked for. Each of
the six core layers carries three to four minutes: the idea, one number, and
what breaks if it is got wrong. The twelve side and outer panels take a minute
each.

**Do not read the file lists aloud.** They are there for someone who asks.

Bracketed text is stage direction. **Arrow keys** move; in the review, **number
keys 1–9** jump straight to a finding, which is what you want when someone asks
about one specifically.

**Before the meeting:** open both files on the machine you will present from,
and press through every panel once. They are static HTML and will not fail, but
that is not a reason to find out in the room.

---

# Segment 1 — where this stands (5 min)

Before either file. No slides.

> Three things before the code.
>
> **First: no films were deposited.** I did not have tool access. Everything I
> am about to show produces model output, and the framework's own validation
> puts its median error at thirty per cent against traceable literature.
>
> **Second: the most useful thing it did was not ranking candidates.** It was
> finding four defects in the weighting we proposed, two citations that cannot
> be traced, and one measurement that contradicts a physical limit. Those do
> not depend on any experiment.
>
> **Third: it identified the measurement that would falsify it.** One X-ray
> scan, one film, an afternoon — and it answers three questions at once. That
> is what I would most like out of this meeting.

[Say the no-films part first, unprompted. It removes the only awkward moment,
and everything after reads as candour rather than defence.]

---

# Segment 2 — the map (25 min)

## Opening (1 min)

[Open `project_map.html`. Layer 0 is showing.]

> A hundred and nineteen files, and the thing worth knowing before any of them
> is that the dependency order runs one way.
>
> **Nothing below optics knows what a coating is.** The solver takes a stack of
> complex indices and a wavelength — it would work for a laser mirror. The
> domain knowledge lives in the layers above, and that is deliberate: it is why
> the optics could be validated against closed-form answers rather than against
> my own expectations of what a Low-E stack should do.

## Layer 0 — provenance as a type (2 min)

> The leaf has no dependencies: constants, the weighting curves, and this.
>
> Every quantity in the framework carries an evidence grade — measured,
> literature, model, hypothesis, and six others — and there is a function that
> **refuses** to admit hypothesis-grade values into a headline table.
>
> The brief itself cautions against putting DFT numbers for the dilute titanium
> ternary into a thesis as though they were established. This makes that a type
> constraint rather than a footnote, so it survives contact with a spreadsheet.

> It did real work. It is what kept those titanium predictions out of the
> results tables when I was tempted.

## Layer 1 — the correction worth learning from (4 min)

[Press **down**.]

> Optical constants, from the standard Lorentz–Drude fits. One deliberate
> departure, and it is the most instructive mistake in the project.
>
> Rakić's published damping for silver implies a DC resistivity of
> **4.4 microhm-centimetres against a true 1.587** — a factor of 2.8. Not
> because the fit is wrong, but because in the visible the Drude term trades
> off against the interband oscillators. The number is a fitting parameter, not
> a physical one.
>
> I used it, and multiplied it by a thin-film size-effect ratio. That counts
> the same scattering twice. **It inflated modelled emissivity roughly
> threefold.**

[Pause.]

> The fix is to re-anchor the free-electron damping to measured DC resistivity
> and let the oscillators handle the interband part. It is in the methodology
> document with the arithmetic, because anyone building on published optical
> fits will hit exactly this.

## Layer 2 — the size effect, and the framework's largest error (4 min)

[Press **down**. The table is on screen.]

> Fuchs–Sondheimer for surface scattering, Mayadas–Shatzkes for grain
> boundaries. The magnitude is easy to underestimate: a ten-nanometre silver
> film is **2.79 times more resistive than bulk**.
>
> That single fact caught one of the brief's transcribed values. Section seven
> quotes 1.59 microhm-centimetres for a ten-nanometre silver film. Bulk silver
> is 1.587. A film that thin cannot reach bulk resistivity — the mean free path
> is fifty-three nanometres, so surface scattering alone forces a ratio above
> two.
>
> I traced it to the source patent. The paper says **1.29**, not 1.59. And 1.29
> is *below* bulk, which is impossible at any thickness. So the brief
> mistranscribed it, and the correct value is more anomalous, not less.

> This layer is also where the framework's largest known error lives. It
> under-predicts sputtered copper sheet resistance by roughly **eightfold**,
> and six of the leading candidates are copper-based. I will come back to that.

## Layer 3 — how we know the optics is right (4 min)

[Press **down**.]

> The solver: arbitrary layers, complex indices, both polarisations, oblique
> incidence. Vectorised, which is why a hundred-and-sixty-eight-point
> composition series with the geometry re-optimised at every point finishes in
> minutes rather than hours.
>
> **How we know it is right is not by inspection.** Four checks against answers
> that can be written down in closed form.

[Point at the table.]

> A bare glass interface must give the Fresnel value. It agrees to five decimal
> places. A quarter-wave layer at the geometric mean index must give an exact
> null. Reflectance plus transmittance plus absorption must equal one — it does,
> to one part in ten billion, on absorbing stacks. And s and p polarisation
> must coincide at normal incidence.
>
> Those are the tests worth having. They check that the model obeys physical
> law, not that a function returns the right type.

> On top of that, the European standards: EN 410 for transmittance, EN 12898
> for emissivity weighted against a 283-kelvin Planck radiance, EN 673 for the
> U-value. Those are the numbers a glazing spec is written in.

## Layer 4 — scoring, and the diagnostics that audit it (5 min)

[Press **down**. This is the layer to spend most on.]

> Derringer–Suich desirability, aggregated geometrically. That choice is not
> cosmetic: a candidate scoring zero on any one criterion goes to zero overall.
> A weighted arithmetic sum does not do that — a zero forfeits only that
> criterion's weight.
>
> The brief asks that the weighting prevent a candidate winning "simply because
> it has excellent conductivity while being unacceptable optically." A weighted
> sum cannot deliver that. A geometric mean can.

> **But the valuable part of this layer is that it audits its own inputs.**

[Point at the correlation table.]

> Emissivity and sheet resistance correlate at 0.978 across the candidate set.
> They are the same free-carrier response of the same layer. Weighting them
> separately put forty per cent of the total on one physical property.
>
> Silver mass and metal cost correlate at **1.000** — silver dominates the metal
> cost so completely that cost is the same number in different units. Supply
> risk at 0.991, for the same reason.
>
> Three criteria that are one quantity, carrying thirty-six per cent of the
> weight between them.

> Six defects in total. Four in the table as proposed, and two more that I only
> found by re-auditing my own corrections to the first two. I will show you the
> code for one of those in the second half.

## Layer 5 — search, and where the wall is (4 min)

[Press **down**.]

> Nelder–Mead thickness optimisation, and composition series with the geometry
> re-optimised at every composition.
>
> That re-optimisation matters more than it sounds. An early conclusion of mine
> — that there was an optimum at sixty per cent silver — was an artifact of
> three sample points at fixed geometry. At five per cent resolution with the
> geometry free, the curve is monotonic and every optimum sits between zero and
> ten per cent silver.

> **And this is where the answer to the brief's actual question is.**

[Point at the two-row table.]

> Thin the silver in AZO/Ag/AZO and at ten nanometres it is continuous, sheet
> resistance 4.18. At nine and a half, it is **discontinuous** — 5.90 and
> climbing.
>
> Percolation is the binding constraint, not transmittance, not emissivity, not
> sheet resistance. A five per cent thickness reduction costs forty-one per cent
> in sheet resistance.
>
> So on the brief's own terms — thin the layer, keep everything else — the
> answer is **about half a nanometre**. That is a negative result and it is
> worth stating plainly. The eighty-two per cent reduction I do have comes from
> changing the composition, not the thickness.

## Beside the stack (4 min)

[Press **down** through the seven side panels. A minute or less each; stop
properly only on `ml/`.]

> These sit beside the stack rather than in it, and **nothing in the core
> imports any of them**. Delete the whole ML subpackage and the framework still
> evaluates every candidate. That matters for handover: the experimental parts
> are the isolated parts.

> Materials Project client — it established that Ag–Cu has no stable ordered
> compound. DFT input generation, never executed: no licence. Design of
> experiments, with a sputter model that refuses to give absolute rates before
> calibration on the real tool. Predicted XRD, which I will come back to at the
> end.

[Stop on `pvdlowe/ml`.]

> This is the one from your August suggestion. It is gated — it must reproduce
> two known Materials Project hull distances before any prediction is accepted.
>
> It produced the Ag–Cu mixing energies, which is a real result. And it
> **failed twice** at the nucleation question, once on lattice mismatch and
> once on termination sensitivity. Both failures are documented with the
> diagnostic that caught them, because a failed calculation with a named cause
> is worth more than silence.

## Around the code (3 min)

[Press through `data/`, `tests/`, `docs/`. Then stop.]

> One thing in `data/` I would flag. The two weighting files are inputs, not
> settings, and they disagree — the heating and cooling profiles share one
> candidate out of ten in their top-ten lists. **A ranking from this framework
> is meaningless without the weighting file that produced it.** That is not a
> caveat; it is a property of multi-objective scoring.

> A hundred and thirty-three tests, and most are about physics rather than
> interfaces. Plus a guard for every defect that has been fixed.
>
> And fifteen documents, of which three record a source that *corrected* the
> model rather than confirming it. That is the part I would point a successor
> at first.

---

# Segment 3 — the review (18 min)

> This is a review of my own code, so treat it accordingly — the ones I did not
> find are still in there.

> Ten places worth stopping on. Six defects, four decisions that should survive
> a refactor. **Every line on screen is read from the repository**, not
> retyped, so what you are looking at is what runs.

[Panel 1. This is the one to spend time on.]

## 1 — the coupling (3 min)

> Film resistivity feeds the Drude damping. A metal layer too thin to conduct
> is automatically a layer that reflects badly.

> Without that coupling, if you optimise for visible transmittance the answer
> is always *make the silver thinner*, and the model reports an excellent
> coating that does not exist. With it, thinning is penalised twice — in sheet
> resistance and in emissivity — because those are two faces of the same
> free-carrier physics.

[If there is a terminal available, run the four-thickness demo from
`docs/CODE_WALKTHROUGH.md` §1 here. If not, the panel says it.]

> The reason this is the first panel: decouple those two and every interface
> test still passes while the model becomes nonsense.

## 2–3 — the other things not to break (2 min)

[Press **down** twice. Move quickly.]

> Geometric aggregation rather than a weighted sum — a candidate scoring zero
> on any criterion goes to zero overall, which is what the brief asks for and
> what an arithmetic sum does not do.

> And four functions that refuse rather than guess. The sputter model when
> uncalibrated, the Materials Project client offline, the surrogate with no
> backend, and this one above four per cent lattice mismatch. Each was tempting
> to make helpful; each would have produced fabricated data.

## 4 — M1, and why the test mattered (3 min)

[Press **4**.]

> Two builders for the same record, differing by ten keys — three of them
> scored criteria. Harmless only because those three are `None` for every
> candidate today.

> **But fixing the construction was not enough.** The emitted frame renamed a
> criterion and dropped three others, so re-scoring a composition series would
> have silently lost a quarter of the weight. I had read that code. The guard
> test found it.

## 5–6 — M2 and M3 (2 min)

> The optimiser caught bare `Exception` and returned a sentinel, which made a
> bug indistinguishable from a bad design. Narrowed and counted — and it now
> reports **zero failures across 1,284 evaluations**, which confirms the branch
> was dead protection. That is why a failure there would almost certainly be a
> bug.

> And a cache that advertised memoisation it did not do, while the actual hot
> path rebuilt every dispersion object on every call. Implemented rather than
> deleted: two hundred repeat calls now take a millisecond.

## 7–8 — the ML module, and the defect a test caught (3 min)

[Press **8**. This is the second one to slow down for.]

> The surrogate module shipped with no coverage of its numerical paths, because
> MACE cannot be installed where the suite runs.

> The way out was to notice that the defects there were never in the energy
> evaluations — those are the model's job and are gated at runtime. They were
> in the **judgement applied to the results**, and that is pure logic over
> tables. Extracting it made it testable without a backend.

> And writing those tests found this. AZO and GZO share a crystalline proxy, so
> they return identical energies — which sorts first is arbitrary. The verdict
> named GZO and concluded *not consistent with the measured ordering*, when
> AZO, the measured winner, was tied with it at the same value.

> **Third time that function's judgement was wrong, and the first time a test
> caught it rather than me reading the output.**

[Pause here. This is the most useful sentence in the session.]

## 9–10 — the diagnostics, and the honest ending (2 min)

> The redundancy diagnostic was itself wrong — it flagged correlated pairs
> whether or not both carried weight, which buries the cases that matter.
> Fixing it exposed that silver mass, metal cost and supply risk are the same
> quantity three times over, carrying thirty-six per cent of the weight.

[Press **10** to finish.]

> And the last one is not a defect. The silver weight of 0.15 is a judgement,
> not a measurement, and it selects the answer — at zero the winner carries
> 0.065 grams per square metre, at 0.30 it carries none, and it changes three
> times in between.

> So the honest output is the sweep, not a ranking. Which of those is right is
> a decision about how much silver consumption matters to Saint-Gobain, and
> that is not the framework's to make.

---

---

# Segment 4 — what it found, and the one question (7 min)

[Close the browser. This part is spoken.]

> Six findings, in descending order of how confident I am.

> **The climate decides the answer, and the brief does not specify one.** Add
> the solar-gain metrics and the two top-ten lists share one candidate out of
> ten. For a heating climate the answer is a nitride stack at five per cent
> silver; for India it is copper with no silver at all — but that one does not
> meet the transmittance spec.

> **The composition optimum is five to fifteen per cent silver, not seventy.**
> Supported three independent ways: least silver, best score under the
> corrected weighting, and — from the mixing energies — the weakest
> thermodynamic tendency to phase-separate. In the dilute corner the driving
> force to separate falls *below* thermal energy at deposition.

> **No single-metal architecture reaches solar-control performance.** Best
> light-to-solar-gain across all thirty-eight candidates is 1.37, against about
> 2.0 commercial. Two metal layers reach 1.76. That is an architectural limit
> and no compositional search would have found it.

> **The dielectric changes the metal, not just the interference stack.** I had
> this backwards and a measurement corrected me. Then a patent — read in full —
> showed silver grows twenty-five-nanometre grains on crystalline zinc oxide
> against fifteen on an amorphous oxide, with the film on the amorphous
> underlayer *discontinuous* where the seeded one was continuous.

> That last one gives me the most consequential single statement in the work:
> **the framework models each metal layer as though the layer beneath it did
> not shape its microstructure.** That one omission accounts for both the
> empirical growth factor and the eightfold copper error. They are one effect
> appearing twice, not two separate caveats.

## The ask

> **One X-ray scan, one film, an afternoon.** It measures the grain size that
> is the common cause of both, tests the templating directly, and discriminates
> the two microstructure hypotheses by a second independent route — peak count
> rather than a number. The framework predicts what the scan should show under
> each hypothesis, so it can be planned rather than interpreted afterwards.

## The question

> And one thing only you can answer. The report benchmarks against a
> ten-nanometre AZO/Ag/AZO at emissivity 0.060, which came from the brief. Our
> own patents claim twelve and a half to sixteen nanometres targeting below
> 0.038 — which this model says needs fourteen to sixteen.
>
> If that is closer to what we actually run, the silver-reduction figures need
> re-baselining against it. **Which is the right reference?**

---

# Questions to expect

**"How much of this would I need to understand to change something?"**
> `optics/stack.py` for the central object, `electrical/thinfilm.py` for the
> coupling, `screening/scoring.py` for how candidates rank. That is most of it.
> Everything in the side column is optional and independent.

**"A hundred and thirty-three tests on ten thousand lines — is that enough?"**
> It is not a coverage figure and I would not claim it as one. The physics
> assertions are the valuable ones. `report/` and `cli.py` are thinly covered,
> and the geometry code in the ML module is exercised by runs on Vertex AI
> rather than by the suite — that is stated in the review rather than glossed.

**"Which of these worried you most?"**
> The one on panel 4, because it was invisible. Everything scored identically,
> every test passed, and it would have stayed that way until someone populated
> a criterion. Nothing about the output would have looked wrong.

**"Did you write these pages by hand?"**
> No — `docs/build_interactive.py` generates both from the repository. Every
> description in the map is a file's own docstring and every excerpt in the
> review is read from source at build time. Three times in this project a
> pasted table drifted from the values that produced it, so anything that can
> be generated is.

---

# Delivery notes

**Do not read the file lists aloud.** They are reference material for someone
who asks, not content.

**Two panels deserve time: 1 and 8.** The coupling is the design decision
everything rests on; the tie-handling defect is the argument for writing tests
rather than re-reading code. The other eight can move at a panel a minute.

**If the session is cut to five minutes:** the map's dependency stack, then
panels 1, 4 and 8.

**Regenerate before presenting** if the code has changed since these were
built:

```bash
python docs/build_interactive.py
```
