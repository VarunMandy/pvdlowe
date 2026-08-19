# Briefing script — technical report walkthrough

For a 12–15 minute presentation with questions. Bracketed text is guidance, not
speech. Bold is emphasis when speaking.

**Bring:** the report (printed or on screen), and `experiments/BENCH_cu_series.md`
as a separate handout — it is the thing you want left on the table afterwards.

---

## 0. Framing — 45 seconds

> I built the screening framework the brief describes, and then used it on the
> brief itself. I want to be straightforward at the start: **no films were
> deposited.** I didn't have tool access. So everything I'm going to show you is
> a model output, and I'll be explicit about where that matters.
>
> What I think is worth your time is less the candidate list and more three
> things the framework found when it was pointed at our own assumptions.

[Say the no-films part *first*, in your own voice, before anyone has to ask. It
removes the only awkward moment in the meeting and buys you credibility for
everything after. Do not apologise for it — state it and move on.]

---

## 1. What was built — 1 minute

> It implements the workflow in section 21: element screening, Materials
> Project, optical multilayer modelling, design of experiments, and the
> multi-objective ranking. Transfer-matrix optics, EN 410 and 673 and 12898
> integration, Fuchs–Sondheimer and Mayadas–Shatzkes transport.
>
> The part I'd point to is that **the transport model feeds back into the
> optics.** The film resistivity sets the Drude damping. So a metal layer too
> thin to conduct is automatically a layer that reflects badly. Without that
> coupling, if you optimise for transmittance the answer is always "make the
> silver thinner", and the model happily reports an excellent coating that
> doesn't exist.
>
> It's about twelve thousand lines, eighty-nine tests, and it's in a repository
> with the documentation and the raw results.

[If they're not interested in implementation, this is where they'll say so.
Let them cut you short — the next section is the substance.]

---

## 2. Finding one: the weighting scheme — 3 minutes

> The first thing I did was encode section 14's weighting table literally. That
> turned out to be the wrong instinct, and it's the finding I'd most want you to
> see.
>
> **The table has no line for silver consumption.** Sections 17 and 20 both name
> minimising silver as an objective, but the weighting table doesn't include it.
> So in the literal encoding, silver mass was computed, displayed, even reported
> as the limiting criterion — and contributed nothing to the score.
>
> The thickness optimiser found that immediately. It returned a design using
> **twenty-nine per cent more silver than our benchmark, and scored it a hundred
> out of a hundred.**

[Pause here. This is the single most memorable fact in the project. Let it sit.]

> There were three more. Emissivity and sheet resistance correlate at
> **0.996** across the candidates — they're both the free-carrier response of the
> same layer — so weighting them separately puts forty per cent of the total on
> one physical property. The targets were set at the specification *minimum*, so
> the criteria went flat exactly where candidates start to differ. And the
> supply-risk band was too narrow to discriminate at all.
>
> All four are corrected and documented in the weighting file. None of it is a
> silent change — the report says what was changed and why.

[Tone matters here. Your supervisor may have written or approved section 14.
Frame it as *the framework found this*, not *this was wrong*. The phrase
"encoding it literally turned out to be the wrong instinct" puts the error on
your approach rather than on their document, which is both diplomatic and
accurate — the brief contradicts itself between sections, and a human reader
would have silently resolved that contradiction.]

---

## 3. Finding two: the literature — 2 minutes

> Second, I checked the citations. All eight sources are now located.
>
> **Two of them I could not match to any paper.** The 85.4 per cent
> transmittance figure and the 78.7 per cent one don't appear in either
> AZO/Ag/AZO study I found. My recommendation is that we don't cite those two
> until someone establishes where they came from.
>
> More seriously — section 16 concludes that a silver-free stack may already
> meet our emissivity target, and that rests on one measurement: the Applied
> Surface Science paper reporting emissivity 0.055 at 9.96 ohms per square.
>
> Those two numbers are hard to hold at once. For a conducting sheet thinner
> than the wavelength, far-infrared reflectance is fixed by sheet resistance
> alone — it comes out of the impedance of free space, with no fitted parameter.
> At 9.96 ohms per square the floor is about **0.096**. The reported 0.055 would
> need roughly five and a half ohms per square.
>
> I tested four explanations. Different samples — no, the abstract attributes all
> three values to one film. Transcription error — no. The glass refractive index
> assumption — no, the limit barely moves. And a band-limited emissometer, which
> was my own best guess — that one I implemented and tested, and **it moves the
> discrepancy the wrong way.** It makes it worse.
>
> The same group reports the same ratio in two other papers. So it looks
> systematic rather than a one-off. What I couldn't check is whether their
> emissivity is normal or hemispherical — that needs the full text, which is
> paywalled.

[If they ask "so is the paper wrong?" — the honest answer is: *I don't know, and
I'm not claiming that. I'm saying the two numbers as published are inconsistent
with a limit that doesn't depend on any model, and the most likely benign
explanation has been tested and eliminated. Before we build a programme on
section 16, someone should read that paper.*]

---

## 4. Finding three: the design space — 4 minutes

> Third, the actual screening. Three results.
>
> **The composition optimum is five to fifteen per cent silver, not seventy.**
> I ran the full range at five per cent steps, re-optimising the layer geometry
> at every composition, under both microstructure models and both dielectrics.
> Eight curves. Every one peaks between zero and ten per cent. Ag70Cu30 is beaten
> in all eight.
>
> I want to be precise about what that is: it's a **sustainability** result, not
> a performance one. Emissivity and sheet resistance keep improving up to fifty
> per cent silver. The score falls because silver mass is weighted. So the trade
> is about half a per cent of emissivity for an eighty-seven per cent cut in
> silver — and that's only the right trade because we decided silver matters.

[This distinction is what separates a defensible recommendation from an
overclaim. Make it explicitly.]

> **Second: the dielectric was the limiting choice, not the metal.** I screened
> fifty-eight metal systems at fixed AZO and only pure silver met the full
> specification — copper failed on transmittance alone. Then I let the
> dielectric vary, and **silicon nitride gains nine points of transmittance on
> copper.** Every metal improves, so it's a property of the dielectric.
>
> Silicon nitride is what industrial Low-E actually uses. The reason it wasn't
> in our search is structural: the brief starts from the periodic table and the
> Materials Project, and both of those surface oxides. Nitrides fall outside
> that framing.
>
> **Third, and this is the one I'd want a decision on: the climate reverses the
> ranking.** The brief doesn't specify a climate, and the weighting doesn't
> constrain solar heat gain — which quietly encodes a heating-dominated
> assumption. When I added the EN 410 solar gain metrics and scored again, the
> top-ten lists under the two climates **share no candidates at all.** Not one.
>
> Every heating-climate entry uses silicon nitride. Every cooling-climate entry
> uses a conductive oxide. And the reason is physical — AZO's free carriers put
> a plasma edge at 1.25 microns, inside the solar band. The conductive oxide is
> doing solar-control work that a passive nitride can't.
>
> So for Northern Europe the answer is a nitride stack at five to ten per cent
> silver. For India it's AZO/Cu/AZO with no silver at all — but it only reaches
> 0.738 transmittance, so it doesn't meet the specification.
>
> That's the honest state of the Indian answer: **the framework is ranking
> near-misses.** No single-metal architecture clears the transmittance target at
> acceptable solar gain. Two metal layers get closer — a double copper stack
> scores highest of anything on that profile — but it still falls short.

[If the application is definitely Indian glazing, this is the most important
slide in the deck and everything else is context. Know which case you're in
before the meeting.]

---

## 5. The gap, and what closes it — 2 minutes

> Now the part that qualifies all of it.
>
> The framework validates well against silver stacks in the infrared — within
> half a per cent on the benchmark it reproduces best. **It fails on copper.** It
> under-predicts sputtered copper sheet resistance by about a factor of eight
> against literature.
>
> Classical size effects can't produce a gap that large. So it's pointing at
> something the model doesn't contain — most likely oxygen incorporated during
> deposition, or much poorer grain structure than silver on the same underlayer.
>
> **If that reading is right, it's good news.** It means copper's problem is film
> quality, not physics — base pressure, seed layers, deposition temperature.
> That's an engineering problem with known levers, and a much more tractable
> target than replacing silver's electronic structure.
>
> But it's currently unresolved, and it gates six of the top candidates in both
> climates.
>
> So I specified the experiment that settles it. Eight capped trilayers, a
> silver control, half a day of tool time. The decision rules are written down
> **before** any data exists — four possible outcomes, each with what it means
> and what to do next, including the one where the literature is right and six of
> my candidates fall over. The analysis is one command.
>
> I validated the analysis on synthetic data with known answers — all four cases
> diagnose correctly. And it's written as a handover document, so someone with
> tool access can run it without me.

[Hand over `BENCH_cu_series.md` at this point. Physical handover of a document
changes the register of the conversation from "here's what I did" to "here's
what's ready to run".]

---

## 6. Close — 45 seconds

> So, briefly: the candidate rankings are hypotheses for prioritising
> experiments, not results, and I'd rather they were read that way. The findings
> I'd actually stand behind are the four weighting defects, the two citations we
> shouldn't use, the measurement that contradicts a physical limit, and the fact
> that nitrides and multi-layer stacks were outside the search framing and beat
> what was in it.
>
> And the thing I'd most like to leave you with is the experiment. It's half a
> day, and it either confirms six candidates or kills them.

---

# Anticipated questions

**"Why didn't you deposit anything?"**
> I didn't have tool access during the internship. I raised it as a limitation
> rather than working around it, and what I did instead was specify the
> experiment tightly enough that someone else can run it — including the
> decision rules, so the interpretation is fixed in advance.

**"So we can't use any of these numbers?"**
> The rankings, no — not as results. What you can use is the ordering, to decide
> what to deposit first. And the weighting and citation findings don't depend on
> any measurement; those stand on their own.

**"Are you saying the brief was wrong?"**
> No. I'm saying the weighting table and sections 17 and 20 don't agree with each
> other about whether silver consumption is an objective, and a human reader
> resolves that automatically where a scoring function can't. That's what the
> framework surfaced. The same for the citations — those are transcription and
> sourcing issues, not judgement errors.

**"How confident are you in the silicon nitride result?"**
> The mechanism I'm confident about — index matching around a metal layer, and
> every metal improves the same way. The absolute numbers less so: the nitride
> optical constants are estimates, not measurements. I'd want measured n and k
> before quoting a transmittance to three figures.

**"What would you do with another three months?"**
> The copper measurement first, because it decides the most. Then the
> microstructure film — one sample settles a question half the candidate table
> depends on. Then finer optimisation of the double-layer stack, because the
> transmittance gap there is eight points and the search I ran was coarse.

**"Is this useful to anyone after you leave?"**
> That's what I optimised for at the end. It's in a repository with tests, the
> documentation explains the physics and the approximations, the protocol is
> written for handover, and the analysis runs in one command. Someone picking it
> up doesn't need me.

**"Why should I trust a model that got copper wrong by eight times?"**
> Because it's the model that told us. The validation is built in and it flags
> its own worst failure. A model that agreed with everything would be less
> useful — I'd have no idea where it was weak. That's also why the experiment
> exists.

[This last one may not be asked out loud but is likely to be thought. Be ready
for it.]

---

# Delivery notes

**Lead with the missing films.** Volunteering a weakness before it's discovered
is the difference between a limitation and a gap.

**Do not defend the candidate rankings.** They're the least durable thing in the
report. If someone attacks them, agree — they're model outputs on uncalibrated
parameters, and that's exactly why the experiment matters.

**Do defend the pre-registration.** Writing decision rules before seeing data is
unusual in materials screening and it's the strongest methodological point you
have. If it comes up, explain that it stops the interpretation being chosen to
suit the result.

**Have one number ready for every claim.** 0.996 correlation. Twenty-nine per
cent more silver at a perfect score. Nine points of transmittance. Zero overlap
between top-ten lists. Factor of eight on copper. Specifics land; summaries
don't.

**If time is cut to five minutes:** the weighting defect, the climate reversal,
and the experiment. Drop everything else.
