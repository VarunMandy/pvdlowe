"""Predicted X-ray diffraction signatures for the metal layer.

Two open questions in this project are answered by the same scan, and this
module says in advance what each answer would look like.

**The microstructure question** (FINDINGS §3.1, report §8.3). If Ag-Cu
segregates, the film contains two fcc phases and the pattern shows two peak
sets at the pure-element positions. If it is a metastable solid solution, there
is one fcc phase with a lattice parameter interpolating between them by
Vegard's law, and one peak set at an intermediate angle. The two cases are
several degrees apart in 2-theta, which any laboratory diffractometer resolves.

That is a **qualitatively different** measurement from the sheet-resistance
discriminator already specified. Sheet resistance distinguishes the hypotheses
by a number (6.4 against 2.6 ohm/sq); diffraction distinguishes them by peak
count. Agreeing answers from two unrelated observables is much stronger than
either alone, and both come from one film.

**The grain-size question** (docs/NUCLEATION_MECHANISM.md). Scherrer broadening
gives the crystallite size directly, which is the parameter identified as the
framework's principal structural weakness. The AGC patent measured 25 nm on
ZnO against 15 nm on amorphous titania; those correspond to 0.35 and 0.59
degrees FWHM on Ag(111), a 70% difference.

Positions come from Bragg's law and the fcc structure factor -- no database and
no fitting. Intensities are not modelled: relative peak heights in a sputtered
film are dominated by texture, and a {111}-textured film looks nothing like a
powder. Peak *positions* and *widths* are what this predicts, and they are what
discriminates the hypotheses.
"""

from __future__ import annotations

import numpy as np

#: Cu K-alpha1, angstrom. The K-alpha2 satellite sits about 0.05 deg higher at
#: these angles and is usually stripped by the instrument software.
CU_KALPHA1 = 1.5406

#: Room-temperature fcc lattice parameters, angstrom.
LATTICE_A = {"Ag": 4.0853, "Cu": 3.6149, "Au": 4.0782, "Al": 4.0495}

#: Allowed fcc reflections in ascending order. Mixed-parity indices are
#: forbidden by the fcc structure factor.
FCC_REFLECTIONS = ((1, 1, 1), (2, 0, 0), (2, 2, 0), (3, 1, 1), (2, 2, 2))

#: Scherrer shape factor for roughly spherical crystallites. The Materials
#: Project XRD viewer uses the same value.
SCHERRER_K = 0.94


def two_theta(lattice_a: float, hkl=(1, 1, 1),
              wavelength: float = CU_KALPHA1) -> float | None:
    """Bragg angle in degrees, or None if the reflection is inaccessible."""
    h, k, l = hkl
    d = lattice_a / np.sqrt(h * h + k * k + l * l)
    s = wavelength / (2.0 * d)
    return float(2.0 * np.degrees(np.arcsin(s))) if abs(s) <= 1.0 else None


def vegard_lattice(ag_fraction: float) -> float:
    """Lattice parameter of an Ag-Cu solid solution, by Vegard's law.

    Linear interpolation between the end members. Real solid solutions deviate
    from linearity by a per cent or so, which is small against the 5.2 degree
    separation this is used to resolve.
    """
    x = float(np.clip(ag_fraction, 0.0, 1.0))
    return x * LATTICE_A["Ag"] + (1.0 - x) * LATTICE_A["Cu"]


def scherrer_fwhm(grain_nm: float, two_theta_deg: float,
                  wavelength: float = CU_KALPHA1, k: float = SCHERRER_K) -> float:
    """Peak width in degrees from crystallite size.

        beta = K * lambda / (D * cos(theta))

    Returns the size contribution only. Instrumental broadening adds in
    quadrature and must be measured on a standard (LaB6 or silicon) and
    subtracted before this is inverted. Strain also broadens peaks; separating
    size from strain needs several reflections and a Williamson-Hall plot.
    """
    theta = np.radians(two_theta_deg / 2.0)
    beta_rad = k * wavelength / (grain_nm * 10.0 * np.cos(theta))
    return float(np.degrees(beta_rad))


def grain_size_from_fwhm(fwhm_deg: float, two_theta_deg: float,
                         instrumental_fwhm_deg: float = 0.08,
                         wavelength: float = CU_KALPHA1,
                         k: float = SCHERRER_K) -> float:
    """Invert Scherrer, subtracting instrumental broadening in quadrature.

    The default instrumental width of 0.08 degrees is typical of a laboratory
    powder diffractometer and **should be replaced by a measured value**. It
    matters most for large grains: at 25 nm the size broadening is 0.35 deg and
    the instrument contributes little, but at 100 nm the two are comparable.
    """
    corrected = np.sqrt(max(fwhm_deg**2 - instrumental_fwhm_deg**2, 1e-12))
    theta = np.radians(two_theta_deg / 2.0)
    return float(k * wavelength / (np.radians(corrected) * np.cos(theta)) / 10.0)


def microstructure_signatures(ag_fraction: float = 0.70,
                              grain_nm: float = 15.0,
                              reflections=FCC_REFLECTIONS) -> "pd.DataFrame":
    """What each microstructure hypothesis predicts, side by side.

    The discriminator is peak **count and position**, not intensity:

    * segregated -> two peak sets, at the pure Ag and pure Cu angles, whose
      positions do not move with composition
    * solid solution -> one peak set at an intermediate angle that shifts
      linearly with composition

    At Ag70Cu30 the solid-solution (111) sits at 39.5 degrees, 1.4 degrees from
    silver and 3.8 from copper. Both separations are an order of magnitude
    larger than the peak widths at any plausible grain size.
    """
    import pandas as pd
    a_ss = vegard_lattice(ag_fraction)
    rows = []
    for hkl in reflections:
        ag = two_theta(LATTICE_A["Ag"], hkl)
        cu = two_theta(LATTICE_A["Cu"], hkl)
        ss = two_theta(a_ss, hkl)
        if ss is None:
            continue
        rows.append({
            "hkl": "".join(map(str, hkl)),
            "segregated_Ag_2theta": None if ag is None else round(ag, 2),
            "segregated_Cu_2theta": None if cu is None else round(cu, 2),
            "solid_solution_2theta": round(ss, 2),
            "fwhm_deg": round(scherrer_fwhm(grain_nm, ss), 3),
            "shift_from_Ag": None if ag is None else round(ss - ag, 2),
        })
    df = pd.DataFrame(rows)
    df.attrs["ag_fraction"] = ag_fraction
    df.attrs["grain_nm"] = grain_nm
    df.attrs["verdict_rule"] = (
        f"Two peak sets at the pure-element angles means SEGREGATED. One set "
        f"near {rows[0]['solid_solution_2theta']} deg for the (111) means "
        f"SOLID SOLUTION. The separation is "
        f"{abs(rows[0]['shift_from_Ag']):.1f} deg from silver against a peak "
        f"width of {rows[0]['fwhm_deg']:.2f} deg, so the two cases cannot be "
        "confused.")
    return df


def grain_size_ladder(underlayers=None, hkl=(1, 1, 1), metal="Ag") -> "pd.DataFrame":
    """Expected peak width for each candidate grain size.

    Defaults are the values measured by TEM in US 7,632,572: 25 nm for silver
    on crystalline ZnO and 15 nm on amorphous titania. The framework's assumed
    `grain_size_ratio` of 3.0 corresponds to 30 nm in a 10 nm film.
    """
    import pandas as pd
    if underlayers is None:
        underlayers = [("crystalline ZnO / AZO (patent, TEM)", 25.0),
                       ("framework default, ratio 3.0", 30.0),
                       ("amorphous TiOx (patent, TEM)", 15.0),
                       ("amorphous nitride, inferred", 12.0),
                       ("nanocrystalline, Cu hypothesis", 6.0)]
    tt = two_theta(LATTICE_A[metal], hkl)
    rows = [{"underlayer": name, "grain_nm": d,
             "two_theta": round(tt, 2),
             "fwhm_deg": round(scherrer_fwhm(d, tt), 3)}
            for name, d in underlayers]
    df = pd.DataFrame(rows)
    df.attrs["note"] = (
        "Subtract instrumental broadening in quadrature before inverting; "
        "measure it on a LaB6 or silicon standard rather than assuming it.")
    return df


def texture_note() -> str:
    """Why relative intensities are not predicted here."""
    return (
        "Peak intensities are deliberately not modelled. A sputtered metal "
        "film is textured -- the AGC patent reports Ag growing {111} on ZnO "
        "because of the epitaxial match to ZnO{0001} -- so relative heights "
        "differ substantially from a powder pattern, and the degree of "
        "texturing is itself the templating measurement. Compare the observed "
        "(111)/(200) intensity ratio against the powder value of about 2.2: a "
        "much larger ratio indicates {111} texture, and therefore templating "
        "by the underlayer.")


__all__ = ["CU_KALPHA1", "LATTICE_A", "FCC_REFLECTIONS", "SCHERRER_K",
           "two_theta", "vegard_lattice", "scherrer_fwhm",
           "grain_size_from_fwhm", "microstructure_signatures",
           "grain_size_ladder", "texture_note"]
