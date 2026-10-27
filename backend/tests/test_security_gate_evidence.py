from security_gate_evidence import BLOCKED, PASS, evaluate_gates


def test_gate_package_is_complete_but_never_self_authorizes():
    report = evaluate_gates(source_sha="a" * 40, ci_run_id="123")
    assert report["package_complete"] is True
    assert report["gate8_authorized"] is False
    assert report["all_gates_pass"] is False
    assert report["source_commit"] == "a" * 40


def test_gate2_application_attack_surface_is_passed():
    report = evaluate_gates(source_sha="b" * 40)
    gate2 = next(g for g in report["gates"] if g["gate"] == 2)
    assert gate2["status"] == PASS
    assert all(c["status"] == PASS for c in gate2["controls"])


def test_gate1_and_runtime_dependent_gates_remain_blocked():
    report = evaluate_gates(source_sha="c" * 40)
    statuses = {g["gate"]: g["status"] for g in report["gates"]}
    assert statuses[1] == BLOCKED
    assert statuses[4] == BLOCKED
    assert statuses[5] == BLOCKED
    assert statuses[6] == BLOCKED
    assert statuses[7] == BLOCKED


def test_gate3_private_tenant_scope_is_explicitly_not_applicable():
    report = evaluate_gates(source_sha="d" * 40)
    gate3 = next(g for g in report["gates"] if g["gate"] == 3)
    assert gate3["status"] == PASS
    scoped = {c["control_id"]: c["status"] for c in gate3["controls"]}
    assert scoped["G3-PUBLIC-SCOPE"] == PASS
    assert scoped["G3-PRIVATE-ACCESS"] == "NOT_APPLICABLE_FOR_LAUNCH_SCOPE"
    assert scoped["G3-TENANTS"] == "NOT_APPLICABLE_FOR_LAUNCH_SCOPE"



def test_gate6_records_application_rate_and_circuit_controls_as_passed():
    report = evaluate_gates(source_sha="e" * 40)
    gate6 = next(g for g in report["gates"] if g["gate"] == 6)
    controls = {c["control_id"]: c["status"] for c in gate6["controls"]}
    assert controls["G6-RATE"] == PASS
    assert controls["G6-CIRCUIT"] == PASS
    assert gate6["status"] == BLOCKED
