"""Tests for JosephsonJunction-Lab.

Every physics test grades the simulation against a closed form or an
exact SI constant - the same grading the built-in CHECKS suite runs.
"""
import json
import math

import main


# --------------------------------------------------------------- constants
def test_ej_value_and_ghz():
    assert main.E_J == main.HBAR * main.IC / (2.0 * main.E_CHARGE)
    assert abs(main.E_J - 3.2910597827e-22) < 1e-31
    rel = main.relations_report()
    assert 496.0 < rel["E_J_over_h_GHz"] < 497.0


def test_phi0_and_kj():
    assert abs(main.PHI0 - 2.0678338484e-15) < 1e-24
    rel = main.relations_report()
    assert abs(rel["K_J_GHz_per_V"] - 483597.8484) < 0.01
    assert abs(rel["K_J_MHz_per_uV"] - 483.5978484) < 0.001


def test_plasma0_and_classical_regime():
    rel = main.relations_report()
    assert 8.77 < rel["f_p0_GHz"] < 8.78
    assert rel["E_J_over_E_C"] > 1.0e4


def test_resistance_scaling():
    r_od = main.shunt_resistance(main.BETA_OD)
    r_ud = main.shunt_resistance(main.BETA_UD)
    assert abs(r_od - 9.0706391) < 1e-4
    assert abs(r_ud / r_od - 8.0) < 1e-9


# --------------------------------------------------------------- relations
def test_current_relation():
    assert abs(main.supercurrent(math.pi / 2) - main.IC) < 1e-18
    assert abs(main.supercurrent(math.pi / 6) - 0.5 * main.IC) < 1e-18
    assert abs(main.supercurrent(math.pi)) < 1e-18


def test_voltage_and_frequency_relations():
    v = main.phase_voltage(2.0 * math.pi * 1e9)
    assert abs(v - main.PHI0 * 1e9) < 1e-12
    f = main.josephson_frequency(10e-6)
    assert abs(f / 1e9 - 4.8359784841) < 0.001


# --------------------------------------------------------------- washboard
def test_barrier_closed_form():
    assert abs(main.barrier_closed_form(0.0) - 2.0) < 1e-12
    assert main.barrier_closed_form(1.0) == 0.0
    assert main.barrier_closed_form(1.1) == 0.0
    assert main.barrier_closed_form(0.99) < 0.01


def test_barrier_numeric_vs_closed():
    for i in (0.0, 0.5, 0.9, 0.99):
        ext = main.washboard_extrema(i)
        closed = main.barrier_closed_form(i)
        assert abs(ext["barrier_EJ"] - closed) / closed < 1e-6


def test_barrier_monotone_and_well_vanishes():
    barriers = [main.barrier_closed_form(i)
                for i in (0.0, 0.5, 0.9, 0.99, 1.0)]
    assert all(a > b for a, b in zip(barriers, barriers[1:]))
    assert main.washboard_extrema(1.0) is None
    assert main.washboard_extrema(1.1) is None


def test_minimum_at_arcsin():
    ext = main.washboard_extrema(0.5)
    assert abs(ext["phi_min"] - math.asin(0.5)) < 1e-6
    assert abs(ext["phi_max"] - (math.pi - math.asin(0.5))) < 1e-6


# --------------------------------------------------------------- plasma
def test_plasma_measured_vs_theory():
    rows = {row["i"]: row for row in main.plasma_report()["rows"]}
    for i in (0.0, 0.5, 0.9):
        assert rows[i]["rel_error"] < 0.01


def test_plasma_softens_with_bias():
    rows = {row["i"]: row for row in main.plasma_report()["rows"]}
    assert (rows[0.9]["omega_measured_over_wp0"]
            < rows[0.5]["omega_measured_over_wp0"]
            < rows[0.0]["omega_measured_over_wp0"])


# --------------------------------------------------------------- RCSJ I-V
def _iv():
    return {row["i"]: row for row in main.iv_report()["rows"]}


def test_zero_voltage_below_ic():
    iv = _iv()
    for i in (0.5, 0.9):
        assert iv[i]["v_overdamped_beta0.25"] < 0.01
        assert iv[i]["v_underdamped_beta16"] < 0.01


def test_rsj_limit_matches_analytic():
    iv = _iv()
    for i in (1.1, 1.5, 2.0):
        analytic = main.rsj_analytic(i)
        assert abs(iv[i]["v_rsj_limit"] - analytic) / analytic < 0.01


def test_overdamped_capacitive_excess():
    iv = _iv()
    for i in (1.5, 2.0):
        assert 0.0 < iv[i]["od_excess_over_analytic_pct"] < 5.0


def test_iv_monotone_and_underdamped_running():
    iv = _iv()
    assert (iv[1.1]["v_overdamped_beta0.25"]
            < iv[1.5]["v_overdamped_beta0.25"]
            < iv[2.0]["v_overdamped_beta0.25"]
            < iv[3.0]["v_overdamped_beta0.25"])
    assert abs(iv[2.0]["v_underdamped_beta16"] - 2.0) < 0.02
    assert iv[1.5]["v_underdamped_beta16"] > main.rsj_analytic(1.5)


# --------------------------------------------------------------- hysteresis
def test_hysteresis_loop():
    h = main.hysteresis_report()
    assert 0.98 <= h["i_switch"] <= 1.02
    assert h["i_retrap_first_trapped"] < h["i_switch"] - 0.5
    assert h["loop_width"] > 0.6


def test_retrapping_matches_formula():
    h = main.hysteresis_report()
    formula = h["i_retrap_formula_4_over_pi_sqrt_beta"]
    assert abs(formula - 4.0 / (math.pi * 4.0)) < 1e-6
    assert abs(h["i_retrap_first_trapped"] - formula) < 0.08
    assert abs(h["i_last_running_down"] - formula) < 0.08


# --------------------------------------------------------------- Shapiro
def test_shapiro_plateaus():
    plats = {p["n"]: p for p in main.shapiro_report()["plateaus"]}
    for n in (0, 1, 2):
        assert plats[n]["points"] >= 3
        assert abs(plats[n]["v_plateau_over_IcR"] - n) < 0.01
    assert plats[0]["points"] > plats[1]["points"] > plats[2]["points"]


def test_shapiro_voltage_is_phi0_times_f():
    shap = main.shapiro_report()
    plats = {p["n"]: p for p in shap["plateaus"]}
    exact = main.PHI0 * shap["f_rf_GHz"] * 1e9 / 1e-6
    assert abs(plats[1]["V_exact_uV"] - exact) < 0.01
    assert abs(plats[1]["V_plateau_uV"] - plats[1]["V_exact_uV"]) \
        / plats[1]["V_exact_uV"] < 0.01
    assert abs(shap["f_rf_GHz"] - 0.5 * main.F_P0 / 1e9) < 0.001


# --------------------------------------------------------------- classifier
def test_classifier_scenarios():
    rep = main.classifier_report()
    assert rep["dc_subcritical_overdamped"]["knn"] \
        == "superconducting-static"
    assert rep["dc_subcritical_underdamped"]["knn"] == "oscillating"
    assert rep["dc_running_overdamped"]["knn"] == "resistive-running"
    assert rep["dc_running_underdamped"]["knn"] == "resistive-running"
    assert rep["rf_step_n1"]["knn"] == "shapiro-locked"
    assert rep["rf_step_n2"]["knn"] == "shapiro-locked"
    assert all(row["knn"] == row["policy"] for row in rep.values())


def test_classifier_grid_matches_policy():
    for features, label in main.TRAINING_GRID:
        assert main.classify_junction(*features) == label


# --------------------------------------------------------------- gates + seats
def test_hold_gates():
    assert len(main.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in main.HOLD_GATES.values())
    for action in ("real_device_control", "junction_fabrication",
                   "cryogenic_operation", "squid_magnetometer_deployment",
                   "voltage_metrology_claim", "simulation_as_measurement_claim"):
        assert main.gate(action) == "HOLD"
    assert main.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    brains = main.brains_report()
    assert brains["decider"]["can_override_hold"] is False
    assert brains["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert brains["decider"]["model"] == "gemini-argon-4"
    assert brains["advisor"]["can_override_hold"] is False
    assert brains["flow"]["rendered"] is False
    assert brains["flow"]["live"] == 0


# --------------------------------------------------------------- CLI
def test_checks_all_pass():
    checks = main.run_checks()
    assert all(ok for _, ok in checks)
    assert len(checks) == 54


def test_cli_checks_and_holds(capsys):
    assert main.main(["checks"]) == 0
    out = capsys.readouterr().out
    assert "CHECKS 54/54" in out
    assert main.main(["holds"]) == 0


def test_cli_hold_demo_exits_2():
    assert main.main(["hold-demo"]) == 2
    assert main.main(["hold-demo", "junction_fabrication"]) == 2
    assert main.main(["hold-demo", "run_simulation"]) == 0


def test_cli_json_topics(capsys):
    for cmd in ("relations", "washboard", "plasma", "iv", "shapiro",
                "classify", "brains"):
        assert main.main([cmd]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload


def test_determinism():
    assert main.washboard_report() == main.washboard_report()
    assert main.relations_report() == main.relations_report()
    assert main.plasma_report() == main.plasma_report()
