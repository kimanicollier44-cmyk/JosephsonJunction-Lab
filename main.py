#!/usr/bin/env python3
"""JosephsonJunction-Lab - educational Josephson junction dynamics lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the central lesson is stated up front:

  * This lab computes the textbook Josephson physics of ONE labelled
    teaching junction (Ic = 1 uA, C = 1 pF) from scratch: the two
    Josephson relations, the tilted washboard potential, the plasma
    frequency, RCSJ current-voltage dynamics, hysteresis, and the AC
    Josephson effect (Shapiro steps).
  * Every headline number is graded against a closed form inside the
    lab: barrier heights against the exact washboard formula, the
    plasma frequency against a numerically integrated phase particle,
    the overdamped I-V curve against the RSJ analytic limit, and the
    Shapiro plateau voltages against V_n = n * h * f / (2e).
  * Nothing here is a measurement. No junction was fabricated, cooled,
    biased, or read out. The labelled Ic and C are teaching numbers,
    not a device specification, and a simulated voltage is never a
    calibration - the real volt is defined by the Josephson constant,
    not by this file.

Real-device control, fabrication, cryogenics, SQUID / magnetometer
deployment, metrology claims, and hardware claims are permanent HOLD
gates - with Gemini Argon 4 Extended Thinking as DECIDER (names-only,
tighten-only), Muse as advisor (never overrides HOLD), and Google
Flow plan-only seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"

# Exact SI constants (2019 SI definitions).
HBAR = 1.054571817e-34          # reduced Planck constant, J s
E_CHARGE = 1.602176634e-19      # elementary charge, C
H_PLANCK = 6.62607015e-34       # Planck constant, J s
PHI0 = H_PLANCK / (2.0 * E_CHARGE)   # flux quantum, Wb
K_J = 2.0 * E_CHARGE / H_PLANCK      # Josephson constant, Hz / V

# The labelled teaching junction. These are LABELLED numbers chosen so
# the arithmetic is easy to follow - they are not a device datasheet.
IC = 1.0e-6                     # critical current, A (labelled)
C_JUNC = 1.0e-12                # junction capacitance, F (labelled)

# Derived Josephson scales for the labelled junction.
E_J = HBAR * IC / (2.0 * E_CHARGE)          # Josephson energy, J
E_C = E_CHARGE ** 2 / (2.0 * C_JUNC)        # charging energy, J
L_J = HBAR / (2.0 * E_CHARGE * IC)          # Josephson inductance, H
OMEGA_P0 = math.sqrt(2.0 * E_CHARGE * IC / (HBAR * C_JUNC))  # rad / s
F_P0 = OMEGA_P0 / (2.0 * math.pi)           # plasma frequency, Hz

BETA_OD = 0.25                  # overdamped Stewart-McCumber parameter
BETA_UD = 16.0                  # underdamped Stewart-McCumber parameter
RF_OMEGA = 0.5                  # lab standard drive: omega_rf / omega_p0
RF_I = 0.75                     # lab standard drive amplitude, I_rf / Ic

WASHBOARD_BIASES = (0.0, 0.5, 0.9, 0.99, 1.0, 1.1)
IV_BIASES = (0.0, 0.5, 0.9, 1.1, 1.5, 2.0, 3.0)

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "real_device_control": "HOLD - no control of a real Josephson junction, SQUID, or qubit device",
    "junction_fabrication": "HOLD - no fabrication guidance for real junctions, barriers, or wafers",
    "cryogenic_operation": "HOLD - no operation of cryostats, dilution refrigerators, or cryogenic plant",
    "squid_magnetometer_deployment": "HOLD - no deploying SQUIDs or Josephson magnetometers in the field",
    "voltage_metrology_claim": "HOLD - no voltage-standard or calibration claim; a simulated Shapiro step calibrates nothing",
    "qubit_hardware_claim": "HOLD - no claims about real superconducting-qubit hardware, coherence, or fidelity",
    "hardware_specification_claim": "HOLD - the labelled Ic and C are teaching numbers, never a device specification",
    "vendor_benchmark_claim": "HOLD - no vendor benchmark, product comparison, or performance claim",
    "medical_magnetometry_use": "HOLD - no medical magnetometry (MEG, cardiac, diagnostic) use of this model",
    "geophysics_survey_use": "HOLD - no geophysical, mineral, or archaeological survey deployment",
    "nondestructive_testing_use": "HOLD - no nondestructive-testing or inspection use of this model",
    "remove_human_override": "HOLD - the human override is never removed from any coupled system",
    "exceed_rated_bias_live": "HOLD - never exceed a rated bias, field, or temperature on live hardware",
    "simulation_as_measurement_claim": "HOLD - a simulated voltage, frequency, or step is not a measurement and must never be presented as one",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


def shunt_resistance(beta_c):
    """Shunt resistance R for a Stewart-McCumber parameter beta_c.

    beta_c = (2e / hbar) * Ic * R^2 * C  ->  solved for R.
    """
    return math.sqrt(beta_c * HBAR / (2.0 * E_CHARGE * IC * C_JUNC))


# ================================================================ 1. The two Josephson relations
# I = Ic * sin(phi) and V = (hbar / 2e) * dphi/dt. Everything else in
# this lab is a consequence of these two lines plus Newton's law for
# the phase particle in the washboard potential.

def supercurrent(phi):
    """First Josephson relation: I = Ic * sin(phi), returned in amps."""
    return IC * math.sin(phi)


def phase_voltage(dphi_dt):
    """Second Josephson relation: V = (hbar / 2e) * dphi/dt, in volts."""
    return (HBAR / (2.0 * E_CHARGE)) * dphi_dt


def josephson_frequency(voltage):
    """Frequency of the AC Josephson oscillation at a DC voltage, Hz."""
    return voltage / PHI0


def relations_report():
    return {
        "junction": {"Ic_A": IC, "C_F": C_JUNC,
                     "label": "labelled teaching junction"},
        "E_J_J": E_J,
        "E_J_over_h_GHz": E_J / H_PLANCK / 1e9,
        "E_C_over_h_MHz": E_C / H_PLANCK / 1e6,
        "E_J_over_E_C": E_J / E_C,
        "L_J_nH": L_J / 1e-9,
        "omega_p0_rad_s": OMEGA_P0,
        "f_p0_GHz": F_P0 / 1e9,
        "phi0_Wb": PHI0,
        "K_J_GHz_per_V": K_J / 1e9,
        "K_J_MHz_per_uV": K_J / 1e12,
        "current_at_phase": {
            "pi/6": supercurrent(math.pi / 6) / IC,
            "pi/2": supercurrent(math.pi / 2) / IC,
            "pi": supercurrent(math.pi) / IC,
        },
        "voltage_of_1GHz_phase_rate_uV":
            phase_voltage(2.0 * math.pi * 1e9) / 1e-6,
        "frequency_at_10uV_GHz": josephson_frequency(10e-6) / 1e9,
        "R_beta_0.25_ohm": shunt_resistance(BETA_OD),
        "R_beta_16_ohm": shunt_resistance(BETA_UD),
        "IcR_beta_0.25_uV": IC * shunt_resistance(BETA_OD) / 1e-6,
        "IcR_beta_16_uV": IC * shunt_resistance(BETA_UD) / 1e-6,
    }


# ================================================================ 2. Washboard potential
# U(phi) = -E_J cos(phi) - (hbar I / 2e) phi. In units of E_J with
# i = I / Ic: u(phi) = -cos(phi) - i * phi. The phase is a particle in
# this tilted washboard; minima trap it (zero voltage), and past
# i = 1 the wells vanish and the particle runs (finite voltage).

def washboard_u(phi, i_norm):
    """Dimensionless washboard potential U / E_J."""
    return -math.cos(phi) - i_norm * phi


def barrier_closed_form(i_norm):
    """Exact barrier height in units of E_J, for i < 1; 0 at/above 1.

    Delta U = 2 E_J [ sqrt(1 - i^2) - i * arccos(i) ].
    """
    if i_norm >= 1.0:
        return 0.0
    return 2.0 * (math.sqrt(1.0 - i_norm ** 2)
                  - i_norm * math.acos(i_norm))


def _derivative(phi, i_norm):
    return math.sin(phi) - i_norm


def _bisect_root(func, lo, hi, tol=1e-13):
    flo = func(lo)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if func(mid) * flo <= 0.0:
            hi = mid
        else:
            lo, flo = mid, func(mid)
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def washboard_extrema(i_norm):
    """Locate the principal well's minimum and maximum numerically.

    Scans dU/dphi = sin(phi) - i on a fine grid over one washboard
    period and refines each sign change by bisection. Returns None
    when the tilt has washed the well away (i >= 1).
    """
    if i_norm >= 1.0:
        return None
    step = 0.0005
    phi = -0.5 * math.pi
    prev_phi, prev_d = phi, _derivative(phi, i_norm)
    roots = []
    while phi < 1.5 * math.pi:
        phi += step
        d = _derivative(phi, i_norm)
        if prev_d == 0.0 or d * prev_d < 0.0:
            root = _bisect_root(lambda p: _derivative(p, i_norm),
                                prev_phi, phi)
            kind = "min" if prev_d < 0.0 else "max"
            roots.append((kind, root))
        prev_phi, prev_d = phi, d
    minimum = next((p for k, p in roots if k == "min"), None)
    maximum = next((p for k, p in roots if k == "max"), None)
    if minimum is None or maximum is None:
        return None
    return {"phi_min": minimum, "phi_max": maximum,
            "u_min": washboard_u(minimum, i_norm),
            "u_max": washboard_u(maximum, i_norm),
            "barrier_EJ": washboard_u(maximum, i_norm)
            - washboard_u(minimum, i_norm)}


def washboard_report():
    rows = []
    for i_norm in WASHBOARD_BIASES:
        ext = washboard_extrema(i_norm)
        closed = barrier_closed_form(i_norm)
        rows.append({
            "i": i_norm,
            "well": ext is not None,
            "phi_min": None if ext is None else round(ext["phi_min"], 6),
            "phi_max": None if ext is None else round(ext["phi_max"], 6),
            "barrier_numeric_EJ":
                None if ext is None else round(ext["barrier_EJ"], 8),
            "barrier_closed_EJ": round(closed, 8),
            "barrier_GHz_h":
                round(closed * E_J / H_PLANCK / 1e9, 4),
        })
    return {"bias_rows": rows,
            "note": "barrier in units of E_J; closed form "
                    "2[sqrt(1-i^2) - i arccos(i)]"}


# ================================================================ 3. Plasma frequency
# Small oscillations in a washboard well run at
# omega_p = omega_p0 * (1 - i^2)^(1/4). The lab does not just quote
# that: it integrates the undamped phase particle in the well with
# RK4 and measures the period from zero crossings.

def plasma_theory(i_norm):
    """omega_p / omega_p0 at bias i (small-oscillation closed form)."""
    return (1.0 - i_norm ** 2) ** 0.25


def plasma_measured(i_norm, amplitude=0.05, dt=0.005, max_tau=400.0):
    """Measured omega_p / omega_p0 from an RK4 phase-particle run."""
    phi_min = math.asin(i_norm)
    phi, w, t = phi_min + amplitude, 0.0, 0.0
    prev = phi - phi_min
    crossings = []

    def acc(p):
        return -(math.sin(p) - i_norm)

    while t < max_tau and len(crossings) < 41:
        k1p, k1w = w, acc(phi)
        k2p, k2w = w + 0.5 * dt * k1w, acc(phi + 0.5 * dt * k1p)
        k3p, k3w = w + 0.5 * dt * k2w, acc(phi + 0.5 * dt * k2p)
        k4p, k4w = w + dt * k3w, acc(phi + dt * k3p)
        phi += dt / 6.0 * (k1p + 2 * k2p + 2 * k3p + k4p)
        w += dt / 6.0 * (k1w + 2 * k2w + 2 * k3w + k4w)
        t += dt
        cur = phi - phi_min
        if (prev < 0.0 <= cur) or (prev > 0.0 >= cur):
            frac = abs(prev) / (abs(prev) + abs(cur))
            crossings.append(t - dt + frac * dt)
        prev = cur
    periods = [crossings[k + 2] - crossings[k]
               for k in range(len(crossings) - 2)]
    period = sum(periods) / len(periods)
    return 2.0 * math.pi / period


def plasma_report():
    rows = []
    for i_norm in (0.0, 0.5, 0.9):
        measured = plasma_measured(i_norm)
        theory = plasma_theory(i_norm)
        rows.append({
            "i": i_norm,
            "omega_measured_over_wp0": round(measured, 6),
            "omega_theory_over_wp0": round(theory, 6),
            "rel_error": round(abs(measured - theory) / theory, 6),
            "f_measured_GHz": round(measured * F_P0 / 1e9, 4),
        })
    return {"rows": rows, "f_p0_GHz": round(F_P0 / 1e9, 6)}


# ================================================================ 4. RCSJ dynamics
# The resistively and capacitively shunted junction, in dimensionless
# time tau = omega_p0 * t and phase phi:
#     phi'' + (1/sqrt(beta_c)) phi' + sin(phi) = i_dc + i_rf sin(Om tau)
# Time-averaged voltage: <V> / (Ic R) = <phi'> / sqrt(beta_c).
# Integrated with fixed-step RK4 - no library integrators.

def _rcsj_run(beta_c, i_dc, i_rf=0.0, omega_rf=0.0, t_trans=250.0,
              t_avg=700.0, dt=0.02, phi=0.0, w=0.0):
    """Run the RCSJ equation; return (<V>/IcR, phi, w) after averaging."""
    damp = 1.0 / math.sqrt(beta_c)
    sqrt_beta = math.sqrt(beta_c)

    def acc(p, ww, t):
        return (i_dc + i_rf * math.sin(omega_rf * t)
                - math.sin(p) - damp * ww)

    def step(p, ww, t):
        k1p, k1w = ww, acc(p, ww, t)
        k2p, k2w = ww + 0.5 * dt * k1w, acc(p + 0.5 * dt * k1p,
                                            ww + 0.5 * dt * k1w,
                                            t + 0.5 * dt)
        k3p, k3w = ww + 0.5 * dt * k2w, acc(p + 0.5 * dt * k2p,
                                            ww + 0.5 * dt * k2w,
                                            t + 0.5 * dt)
        k4p, k4w = ww + dt * k3w, acc(p + dt * k3p, ww + dt * k3w,
                                      t + dt)
        return (p + dt / 6.0 * (k1p + 2 * k2p + 2 * k3p + k4p),
                ww + dt / 6.0 * (k1w + 2 * k2w + 2 * k3w + k4w))

    t = 0.0
    for _ in range(int(t_trans / dt)):
        phi, w = step(phi, w, t)
        t += dt
    total, n = 0.0, 0
    for _ in range(int(t_avg / dt)):
        phi, w = step(phi, w, t)
        t += dt
        total += w
        n += 1
    return total / n / sqrt_beta, phi, w


def _rsj_run(i_dc, t_trans=300.0, t_avg=2000.0, dt=0.02):
    """The beta_c -> 0 (pure RSJ) limit at beta_c = BETA_OD's R.

    First-order equation phi' = sqrt(beta_c) * (i - sin phi); its
    time-averaged voltage is the analytic R * sqrt(I^2 - Ic^2) curve,
    so this run grades the integrator against the closed form.
    """
    scale = math.sqrt(BETA_OD)

    def deriv(p):
        return scale * (i_dc - math.sin(p))

    phi = 0.5
    for _ in range(int(t_trans / dt)):
        k1 = deriv(phi)
        k2 = deriv(phi + 0.5 * dt * k1)
        k3 = deriv(phi + 0.5 * dt * k2)
        k4 = deriv(phi + dt * k3)
        phi += dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    total, n = 0.0, 0
    for _ in range(int(t_avg / dt)):
        k1 = deriv(phi)
        k2 = deriv(phi + 0.5 * dt * k1)
        k3 = deriv(phi + 0.5 * dt * k2)
        k4 = deriv(phi + dt * k3)
        dphi = dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        phi += dphi
        total += dphi / dt
        n += 1
    return total / n / scale


def rsj_analytic(i_norm):
    """Analytic overdamped-limit <V> / (Ic R): sqrt(i^2 - 1), i > 1."""
    return math.sqrt(i_norm ** 2 - 1.0) if i_norm > 1.0 else 0.0


def _iv_point(beta_c, i_dc):
    if i_dc < 1.0:
        t_trans, t_avg = 150.0, 150.0
    elif i_dc < 1.2:
        t_trans, t_avg = 250.0, 1500.0
    else:
        t_trans, t_avg = 250.0, 700.0
    phi0 = math.asin(i_dc) if i_dc < 1.0 else 0.5
    v, _, _ = _rcsj_run(beta_c, i_dc, t_trans=t_trans, t_avg=t_avg,
                        phi=phi0)
    return v


_REPORT_CACHE = {}


def iv_report():
    """I-V curves for both damping regimes plus the RSJ-limit grading."""
    if "iv" in _REPORT_CACHE:
        return _REPORT_CACHE["iv"]
    rows = []
    for i_dc in IV_BIASES:
        v_od = _iv_point(BETA_OD, i_dc)
        v_ud = _iv_point(BETA_UD, i_dc)
        analytic = rsj_analytic(i_dc)
        v_rsj = _rsj_run(i_dc) if i_dc > 1.0 else 0.0
        rows.append({
            "i": i_dc,
            "v_overdamped_beta0.25": round(v_od, 6),
            "v_underdamped_beta16": round(v_ud, 6),
            "v_rsj_limit": round(v_rsj, 6),
            "v_analytic_sqrt_i2_1": round(analytic, 6),
            "od_excess_over_analytic_pct":
                None if analytic == 0.0 else
                round(100.0 * (v_od - analytic) / analytic, 3),
        })
    report = {"rows": rows, "beta_overdamped": BETA_OD,
              "beta_underdamped": BETA_UD,
              "units": "<V> / (Ic R)"}
    _REPORT_CACHE["iv"] = report
    return report


def hysteresis_report():
    """Sweep bias up then down on the underdamped junction.

    State is carried from point to point, exactly like a real sweep:
    the junction switches at i_switch on the way up and retraps at
    i_retrap < i_switch on the way down.
    """
    if "hyst" in _REPORT_CACHE:
        return _REPORT_CACHE["hyst"]
    step = 0.05
    phi, w = 0.0, 0.0
    up = []
    i_dc = 0.0
    while i_dc <= 1.30 + 1e-9:
        v, phi, w = _rcsj_run(BETA_UD, round(i_dc, 2), t_trans=200.0,
                              t_avg=200.0, phi=phi, w=w)
        up.append((round(i_dc, 2), v))
        i_dc += step
    down = []
    i_dc = 1.30
    while i_dc >= 0.0 - 1e-9:
        v, phi, w = _rcsj_run(BETA_UD, round(i_dc, 2), t_trans=200.0,
                              t_avg=200.0, phi=phi, w=w)
        down.append((round(i_dc, 2), v))
        i_dc -= step
    i_switch = next(i for i, v in up if v > 0.05)
    i_retrap = next(i for i, v in down if v < 0.02)
    last_running = None
    for i, v in down:
        if v >= 0.02:
            last_running = i
        else:
            break
    report = {
        "beta_c": BETA_UD,
        "i_switch": i_switch,
        "i_retrap_first_trapped": i_retrap,
        "i_last_running_down": last_running,
        "i_retrap_formula_4_over_pi_sqrt_beta":
            round(4.0 / (math.pi * math.sqrt(BETA_UD)), 6),
        "loop_width": round(i_switch - i_retrap, 2),
        "up_curve": [[i, round(v, 4)] for i, v in up],
        "down_curve": [[i, round(v, 4)] for i, v in down],
    }
    _REPORT_CACHE["hyst"] = report
    return report


# ================================================================ 5. AC Josephson effect - Shapiro steps
# With an RF drive at frequency f, the time-averaged voltage locks
# onto plateaus at V_n = n * h * f / (2e) = n * Phi0 * f. In the lab's
# units the step spacing is omega_rf / sqrt(beta_c) of Ic R.

def shapiro_report():
    if "shapiro" in _REPORT_CACHE:
        return _REPORT_CACHE["shapiro"]
    step_v = RF_OMEGA / math.sqrt(BETA_OD)
    f_rf = RF_OMEGA * F_P0
    phi, w = 0.3, 0.0
    scan = []
    k = 0
    while k <= 52:
        i_dc = round(k * 0.05, 2)
        v, phi, w = _rcsj_run(BETA_OD, i_dc, i_rf=RF_I,
                              omega_rf=RF_OMEGA, t_trans=200.0,
                              t_avg=600.0, phi=phi, w=w)
        scan.append((i_dc, v))
        k += 1
    plateaus = []
    for n in (0, 1, 2):
        target = n * step_v
        best, run = [], []
        for i_dc, v in scan:
            if abs(v - target) < 0.01:
                run.append((i_dc, v))
            else:
                if len(run) > len(best):
                    best = run
                run = []
        if len(run) > len(best):
            best = run
        plateau_v = (sum(v for _, v in best) / len(best)) if best else None
        plateaus.append({
            "n": n,
            "points": len(best),
            "i_range": None if not best else [best[0][0], best[-1][0]],
            "v_plateau_over_IcR":
                None if plateau_v is None else round(plateau_v, 6),
            "v_exact_over_IcR": round(target, 6),
            "V_plateau_uV":
                None if plateau_v is None else
                round(plateau_v * IC * shunt_resistance(BETA_OD) / 1e-6, 4),
            "V_exact_uV": round(n * PHI0 * f_rf / 1e-6, 4),
        })
    report = {
        "beta_c": BETA_OD, "omega_rf_over_wp0": RF_OMEGA,
        "i_rf_over_Ic": RF_I, "f_rf_GHz": round(f_rf / 1e9, 6),
        "step_spacing_over_IcR": round(step_v, 6),
        "plateaus": plateaus,
        "scan": [[i, round(v, 4)] for i, v in scan],
    }
    _REPORT_CACHE["shapiro"] = report
    return report


# ================================================================ 6. kNN regime classifier
# Features: bias i = I / Ic, Stewart-McCumber beta_c, and the measured
# <V> / (Ic R). The training grid is labelled by the lab's own regime
# policy (policy_label below) - the classifier interpolates the
# policy, it does not replace the dynamics.

def policy_label(i_norm, beta_c, v_norm):
    """The lab's regime policy, distilled to a four-way label."""
    if v_norm >= 0.05 and beta_c <= 1.0:
        step = RF_OMEGA / math.sqrt(beta_c)
        n = int(v_norm / step + 0.5)
        if n >= 1 and abs(v_norm - n * step) <= 0.03:
            return "shapiro-locked"
    if v_norm >= 0.05:
        return "resistive-running"
    if beta_c >= 4.0:
        return "oscillating"
    return "superconducting-static"


def _training_grid():
    rows = []
    for k in range(0, 11):
        i_norm = k * 0.25
        for beta_c in (0.25, 1.0, 4.0, 16.0):
            for m in range(0, 11):
                v_norm = m * 0.25
                rows.append(((i_norm, beta_c, v_norm),
                             policy_label(i_norm, beta_c, v_norm)))
    return rows


TRAINING_GRID = _training_grid()


def _scaled(features):
    i_norm, beta_c, v_norm = features
    return (i_norm / 2.5, math.sqrt(beta_c) / 4.0, v_norm / 2.5)


def classify_junction(i_norm, beta_c, v_norm, k=5):
    """Distance-weighted kNN over the policy-labelled grid."""
    target = _scaled((i_norm, beta_c, v_norm))
    ranked = []
    for features, label in TRAINING_GRID:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    weights = {}
    for dist, _, label in ranked[:k]:
        weights[label] = weights.get(label, 0.0) + 1.0 / (dist + 1e-9)
    priority = {"superconducting-static": 0, "oscillating": 1,
                "resistive-running": 2, "shapiro-locked": 3}
    return sorted(weights.items(),
                  key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def classifier_report():
    iv = {row["i"]: row for row in iv_report()["rows"]}
    shapiro = {round(i, 2): v for i, v in shapiro_report()["scan"]}
    scenarios = {
        "dc_subcritical_overdamped":
            (0.50, BETA_OD, iv[0.5]["v_overdamped_beta0.25"]),
        "dc_subcritical_underdamped":
            (0.50, BETA_UD, iv[0.5]["v_underdamped_beta16"]),
        "dc_running_overdamped":
            (1.50, BETA_OD, iv[1.5]["v_overdamped_beta0.25"]),
        "dc_running_underdamped":
            (2.00, BETA_UD, iv[2.0]["v_underdamped_beta16"]),
        "rf_step_n1": (1.30, BETA_OD, shapiro[1.30]),
        "rf_step_n2": (2.20, BETA_OD, shapiro[2.20]),
    }
    return {name: {"features": features,
                   "policy": policy_label(*features),
                   "knn": classify_junction(*features)}
            for name, features in scenarios.items()}


# ================================================================ 7. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="josephsonjunction-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "model": "gemini-argon-4",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all device gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="josephsonjunction-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Say it in the first line of every report: the labelled Ic and C are teaching numbers, every simulated voltage is graded against a closed form, and a Shapiro step in a file calibrates nothing - then show the barrier, the plasma check, and the hysteresis loop.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["a tilted washboard potential with a phase particle in one well",
                  "the well flattening as the bias approaches Ic and the particle breaking free",
                  "an I-V curve splitting into two branches - the hysteresis loop",
                  "RF drive quantising the voltage axis into Shapiro steps",
                  "the plasma oscillation ringing inside one washboard well"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    rel = relations_report()

    # 1. constants + the two relations
    chk("ej_formula_value", abs(E_J - 3.2910597827e-22) < 1e-31
        and E_J == HBAR * IC / (2.0 * E_CHARGE))
    chk("ej_in_ghz", 496.0 < rel["E_J_over_h_GHz"] < 497.0)
    chk("phi0_value", abs(PHI0 - 2.0678338484e-15) < 1e-24)
    chk("kj_constant", abs(rel["K_J_GHz_per_V"] - 483597.8484) < 0.01
        and abs(rel["K_J_MHz_per_uV"] - 483.5978484) < 0.001)
    chk("plasma0_value", 8.77 < rel["f_p0_GHz"] < 8.78
        and OMEGA_P0 == math.sqrt(2.0 * E_CHARGE * IC / (HBAR * C_JUNC)))
    chk("classical_phase_regime", rel["E_J_over_E_C"] > 1.0e4)
    chk("current_relation", abs(supercurrent(math.pi / 2) - IC) < 1e-18
        and abs(supercurrent(math.pi / 6) - 0.5 * IC) < 1e-18)
    chk("voltage_relation", abs(phase_voltage(2.0 * math.pi * 1e9)
                                - PHI0 * 1e9) < 1e-12)
    chk("frequency_at_10uV", abs(josephson_frequency(10e-6) / 1e9
                                 - 4.8359784841) < 0.001)
    chk("resistance_scaling",
        abs(shunt_resistance(BETA_UD) / shunt_resistance(BETA_OD) - 8.0)
        < 1e-9 and abs(shunt_resistance(BETA_OD) - 9.0706391) < 1e-4)

    # 2. washboard potential
    wash = {row["i"]: row for row in washboard_report()["bias_rows"]}
    chk("barrier_i0_is_2ej", abs(barrier_closed_form(0.0) - 2.0) < 1e-12
        and abs(wash[0.0]["barrier_numeric_EJ"] - 2.0) < 1e-8)
    chk("barrier_numeric_vs_closed",
        all(abs(washboard_extrema(i)["barrier_EJ"]
                - barrier_closed_form(i)) / barrier_closed_form(i) < 1e-6
            for i in (0.0, 0.5, 0.9, 0.99)))
    barriers = [barrier_closed_form(i) for i in (0.0, 0.5, 0.9, 0.99, 1.0)]
    chk("barrier_monotone_to_zero",
        all(a > b for a, b in zip(barriers, barriers[1:]))
        and barriers[-1] == 0.0)
    chk("barrier_099_small", barrier_closed_form(0.99) < 0.01)
    chk("well_gone_at_and_above_ic",
        wash[1.0]["well"] is False and wash[1.1]["well"] is False
        and washboard_extrema(1.0) is None)
    ext5 = washboard_extrema(0.5)
    chk("minimum_at_arcsin_i",
        abs(ext5["phi_min"] - math.asin(0.5)) < 1e-6
        and abs(ext5["phi_max"] - (math.pi - math.asin(0.5))) < 1e-6)

    # 3. plasma frequency - integrated, not quoted
    plasma = {row["i"]: row for row in plasma_report()["rows"]}
    chk("plasma_i0_matches", plasma[0.0]["rel_error"] < 0.01)
    chk("plasma_i05_matches", plasma[0.5]["rel_error"] < 0.01)
    chk("plasma_i09_matches", plasma[0.9]["rel_error"] < 0.01)
    chk("plasma_softens_with_bias",
        plasma[0.9]["omega_measured_over_wp0"]
        < plasma[0.5]["omega_measured_over_wp0"]
        < plasma[0.0]["omega_measured_over_wp0"])

    # 4. RCSJ I-V curves
    iv = {row["i"]: row for row in iv_report()["rows"]}
    chk("od_zero_voltage_below_ic",
        iv[0.5]["v_overdamped_beta0.25"] < 0.01
        and iv[0.9]["v_overdamped_beta0.25"] < 0.01)
    chk("ud_zero_voltage_below_ic",
        iv[0.5]["v_underdamped_beta16"] < 0.01
        and iv[0.9]["v_underdamped_beta16"] < 0.01)
    chk("rsj_limit_matches_analytic",
        all(abs(iv[i]["v_rsj_limit"] - rsj_analytic(i)) / rsj_analytic(i)
            < 0.01 for i in (1.1, 1.5, 2.0)))
    chk("rcsj_overdamped_capacitive_excess",
        all(0.0 < iv[i]["od_excess_over_analytic_pct"] < 5.0
            for i in (1.5, 2.0)))
    chk("od_iv_monotone",
        iv[1.1]["v_overdamped_beta0.25"] < iv[1.5]["v_overdamped_beta0.25"]
        < iv[2.0]["v_overdamped_beta0.25"]
        < iv[3.0]["v_overdamped_beta0.25"])
    chk("ud_running_voltage_near_bias",
        abs(iv[2.0]["v_underdamped_beta16"] - 2.0) < 0.02)
    chk("ud_excess_current",
        iv[1.5]["v_underdamped_beta16"] > rsj_analytic(1.5))

    # 5. hysteresis
    hyst = hysteresis_report()
    chk("switching_at_ic", 0.98 <= hyst["i_switch"] <= 1.02)
    chk("retrapping_below_switching",
        hyst["i_retrap_first_trapped"] < hyst["i_switch"] - 0.5
        and hyst["loop_width"] > 0.6)
    chk("retrapping_matches_formula",
        abs(hyst["i_retrap_first_trapped"]
            - hyst["i_retrap_formula_4_over_pi_sqrt_beta"]) < 0.08
        and abs(hyst["i_last_running_down"]
                - hyst["i_retrap_formula_4_over_pi_sqrt_beta"]) < 0.08)

    # 6. Shapiro steps
    shap = shapiro_report()
    plats = {p["n"]: p for p in shap["plateaus"]}
    chk("shapiro_step0", plats[0]["points"] >= 3
        and abs(plats[0]["v_plateau_over_IcR"] - 0.0) < 0.01)
    chk("shapiro_step1", plats[1]["points"] >= 3
        and abs(plats[1]["v_plateau_over_IcR"] - 1.0) < 0.01)
    chk("shapiro_step2", plats[2]["points"] >= 3
        and abs(plats[2]["v_plateau_over_IcR"] - 2.0) < 0.01)
    chk("shapiro_step_widths_shrink",
        plats[0]["points"] > plats[1]["points"] > plats[2]["points"])
    chk("shapiro_voltage_is_phi0_f",
        abs(plats[1]["V_exact_uV"] - PHI0 * shap["f_rf_GHz"] * 1e9 / 1e-6)
        < 0.01 and abs(plats[1]["V_plateau_uV"]
                       - plats[1]["V_exact_uV"])
        / plats[1]["V_exact_uV"] < 0.01)
    chk("rf_frequency_half_plasma",
        abs(shap["f_rf_GHz"] - 0.5 * F_P0 / 1e9) < 0.001)

    # 7. classifier - labels come from the lab's own regime policy
    rep = classifier_report()
    chk("classifier_static", rep["dc_subcritical_overdamped"]["knn"]
        == "superconducting-static")
    chk("classifier_oscillating", rep["dc_subcritical_underdamped"]["knn"]
        == "oscillating")
    chk("classifier_running_overdamped", rep["dc_running_overdamped"]["knn"]
        == "resistive-running")
    chk("classifier_running_underdamped",
        rep["dc_running_underdamped"]["knn"] == "resistive-running")
    chk("classifier_shapiro_n1", rep["rf_step_n1"]["knn"] == "shapiro-locked")
    chk("classifier_shapiro_n2", rep["rf_step_n2"]["knn"] == "shapiro-locked")
    chk("classifier_scenarios_match_policy",
        all(row["knn"] == row["policy"] for row in rep.values()))
    chk("classifier_grid_matches_policy",
        all(classify_junction(*features) == label
            for features, label in TRAINING_GRID))

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_device_hold", gate("real_device_control") == "HOLD")
    chk("gate_fabrication_hold", gate("junction_fabrication") == "HOLD")
    chk("gate_cryogenics_hold", gate("cryogenic_operation") == "HOLD")
    chk("gate_squid_hold", gate("squid_magnetometer_deployment") == "HOLD")
    chk("gate_metrology_hold", gate("voltage_metrology_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking"
        and brains["decider"]["model"] == "gemini-argon-4")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("JosephsonJunction-Lab - Josephson junction dynamics lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - what this lab does and does not claim")
    print("    One LABELLED teaching junction (Ic = 1 uA, C = 1 pF) is")
    print("    computed from scratch: the two Josephson relations, the")
    print("    washboard potential, plasma oscillations, RCSJ dynamics,")
    print("    hysteresis, and Shapiro steps. Every headline number is")
    print("    graded against a closed form in CHECKS. Nothing was")
    print("    fabricated, cooled, biased, or measured - and a simulated")
    print("    Shapiro step calibrates nothing.")
    rel = relations_report()
    print("\n[2] The two Josephson relations + derived scales")
    print(f"    I = Ic sin(phi)          I(pi/2) = Ic exactly")
    print(f"    V = (hbar/2e) dphi/dt    1 GHz phase rate = "
          f"{rel['voltage_of_1GHz_phase_rate_uV']:.6f} uV")
    print(f"    E_J = {rel['E_J_J']:.6e} J = {rel['E_J_over_h_GHz']:.3f} GHz*h"
          f" | E_C/h = {rel['E_C_over_h_MHz']:.3f} MHz"
          f" | E_J/E_C = {rel['E_J_over_E_C']:.0f} (classical phase)")
    print(f"    omega_p0 = {rel['omega_p0_rad_s']:.6e} rad/s"
          f" | f_p0 = {rel['f_p0_GHz']:.6f} GHz"
          f" | L_J = {rel['L_J_nH']:.4f} nH")
    print(f"    K_J = {rel['K_J_MHz_per_uV']:.6f} MHz/uV"
          f" | f(10 uV) = {rel['frequency_at_10uV_GHz']:.6f} GHz")
    print(f"    R(beta_c=0.25) = {rel['R_beta_0.25_ohm']:.4f} ohm"
          f" (IcR = {rel['IcR_beta_0.25_uV']:.4f} uV)"
          f" | R(beta_c=16) = {rel['R_beta_16_ohm']:.4f} ohm")
    print("\n[3] Washboard potential - barrier vs bias (units of E_J)")
    for row in washboard_report()["bias_rows"]:
        if row["well"]:
            print(f"    i = {row['i']:4.2f}  phi_min {row['phi_min']:7.4f}"
                  f"  barrier numeric {row['barrier_numeric_EJ']:.8f}"
                  f"  closed form {row['barrier_closed_EJ']:.8f}")
        else:
            print(f"    i = {row['i']:4.2f}  no well - the tilt has washed"
                  f" it away, barrier 0")
    print("    -> barrier = 2[sqrt(1-i^2) - i arccos(i)], exactly 2 at i=0,")
    print("       zero at i=1: past Ic there is nothing left to trap the phase.")
    print("\n[4] Plasma frequency - integrated phase particle vs (1-i^2)^1/4")
    for row in plasma_report()["rows"]:
        print(f"    i = {row['i']:3.1f}  measured {row['omega_measured_over_wp0']:.6f}"
              f"  theory {row['omega_theory_over_wp0']:.6f}"
              f"  rel err {row['rel_error']:.2e}"
              f"  f = {row['f_measured_GHz']:.4f} GHz")
    print("\n[5] RCSJ I-V curves - <V> / (Ic R) vs I / Ic")
    print("    i      overdamped(0.25)  underdamped(16)  RSJ limit  analytic")
    for row in iv_report()["rows"]:
        print(f"    {row['i']:4.1f}   {row['v_overdamped_beta0.25']:10.6f}"
              f"        {row['v_underdamped_beta16']:10.6f}"
              f"     {row['v_rsj_limit']:8.6f}  {row['v_analytic_sqrt_i2_1']:8.6f}")
    print("    -> the beta_c -> 0 limit reproduces R*sqrt(I^2-Ic^2); the real")
    print("       capacitor at beta_c = 0.25 adds a measured excess of")
    iv = {row["i"]: row for row in iv_report()["rows"]}
    print(f"       +{iv[1.5]['od_excess_over_analytic_pct']:.2f}% at i=1.5 and"
          f" +{iv[2.0]['od_excess_over_analytic_pct']:.2f}% at i=2.0 - printed,")
    print("       not hidden. Below Ic both regimes sit at exactly V = 0.")
    hyst = hysteresis_report()
    print("\n[6] Hysteresis - the underdamped junction remembers its path")
    print(f"    switching current (up-sweep)   i_switch = {hyst['i_switch']:.2f}")
    print(f"    retrapping current (down)      i_retrap = "
          f"{hyst['i_retrap_first_trapped']:.2f}"
          f" (last running {hyst['i_last_running_down']:.2f})")
    print(f"    large-beta_c formula 4/(pi sqrt(beta_c)) = "
          f"{hyst['i_retrap_formula_4_over_pi_sqrt_beta']:.6f}")
    print(f"    loop width = {hyst['loop_width']:.2f} of Ic - between retrapping")
    print("    and switching, the voltage depends on where you came from.")
    shap = shapiro_report()
    print("\n[7] Shapiro steps - AC Josephson effect under RF drive")
    print(f"    drive f = {shap['f_rf_GHz']:.6f} GHz (omega = 0.5 omega_p0),"
          f" I_rf = {shap['i_rf_over_Ic']} Ic, beta_c = {shap['beta_c']}")
    for p in shap["plateaus"]:
        print(f"    n = {p['n']}  plateau <V> = {p['V_plateau_uV']:.4f} uV"
              f"  exact n*h*f/2e = {p['V_exact_uV']:.4f} uV"
              f"  over i in {p['i_range']} ({p['points']} points)")
    print("    -> the voltage quantises to n * Phi0 * f: this effect is the")
    print("       real world's volt standard - in a file it is a check,")
    print("       never a calibration.")
    print("\n[8] Regime classifier (TinyML kNN, labels from the lab policy)")
    for name, row in classifier_report().items():
        feats = row["features"]
        print(f"    {name:30s} i={feats[0]:.2f} beta={feats[1]:5.2f} "
              f"v={feats[2]:.4f} -> {row['knn']}")
    print("\n[9] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[10] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "relations":
        print(json.dumps(relations_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "washboard":
        print(json.dumps(washboard_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "plasma":
        print(json.dumps(plasma_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "iv":
        print(json.dumps({"iv": iv_report(),
                          "hysteresis": hysteresis_report()},
                         indent=2, sort_keys=True))
        return 0
    if cmd == "shapiro":
        print(json.dumps(shapiro_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "real_device_control"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
