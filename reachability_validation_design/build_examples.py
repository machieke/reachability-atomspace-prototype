"""Build illustrative design-contract JSON files; does not run the benchmark."""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def write_json(filename: str, value: object) -> None:
    (HERE / filename).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')

invariants = {
    'hard_acceptance_gates': True,
    'joint_requirement_checks': True,
    'context_and_revision_binding': True,
    'authoritative_operation_ledger': True,
    'resource_reservations': True,
    'external_idempotency_and_reconciliation_contract': True,
    'observed_relief_not_predicted_coverage': True,
    'evidence_lineage_accounting': True,
    'mandatory_dependency_pins': True,
    'same_public_information': True,
}
variants = []
for typed, coverage, transport in itertools.product((False, True), repeat=3):
    variants.append({
        'variant_id': f'P{int(typed)}_L{int(coverage)}_T{int(transport)}',
        'pressure_mode': 'typed_backward' if typed else 'scalar_backward',
        'commitment_aware_planning': coverage,
        'scheduler': 'adaptive_transport' if transport else 'dependency_priority_queue',
        'invariants': invariants,
        'note': 'L0 removes coverage from planning priority; it does not delete actual operations or weaken their contracts.'
    })
write_json('ablation_manifest.example.json', {
    'schema': 'rd-validation-design/0.1',
    'status': 'DESIGN_CONTRACT_NOT_RUNTIME_CONFIGURATION',
    'factorial': '2x2x2: typed pressure x commitment-aware planning x transport',
    'variants': variants,
    'parameter_selection': {
        'frozen_replacement_report': True,
        'equal_budget_retuned_report': True,
        'tune_on': 'development_and_tuning_only',
        'confirm_on': 'locked_parent_instance_cohort',
        'budgets': ['matched_total_wall_time', 'matched_declared_work', 'matched_memory'],
        'oracle_access': 'evaluator_only',
    },
    'required_canaries': [
        'Transport-off variants make zero transport-update calls.',
        'Scalar variants do not inherit typed ranks from a cache.',
        'Coverage-blind variants preserve the authoritative ledger but do not use predicted coverage for priority.',
        'Every variant enforces the same gate policy digest.'
    ],
    'planned_outputs': ['correctness', 'goal_loss', 'durable_completion', 'total_compute', 'interaction_effects_with_intervals'],
})

# This example deliberately keeps test labels and event schedules on the evaluator side.
# Strings in expected assertions are documentation, not an executable assertion language.
events = [
    {'tick': 0, 'phase': 0, 'driver': 'query_deployment_admission', 'expected': ['Unobserved TestPassed does not satisfy the deployment contract.', 'An allowed test observation remains available.']},
    {'tick': 1, 'phase': 0, 'environment': 'deliver_test_pass', 'public_payload': {'artifact_digest': 'sha256:v2-example', 'evidence_id': 'test-e1', 'passed': True}},
    {'tick': 1, 'phase': 1, 'driver': 'certify_candidate_against_credential_rev1', 'expected': ['Candidate certificate binds credential revision 1 and current policy.']},
    {'tick': 2, 'phase': 0, 'environment': 'revoke_credential_rev1', 'public_payload': {'credential_id': 'credential-A', 'revision': 2, 'valid': False}},
    {'tick': 2, 'phase': 1, 'driver': 'dispatch_with_old_certificate', 'expected': ['Stale dispatch is blocked.', 'No deployment effect occurs.', 'The artifact test remains supported.']},
    {'tick': 3, 'phase': 0, 'environment': 'issue_replacement_credential', 'public_payload': {'credential_id': 'credential-B', 'revision': 1, 'valid': True, 'valid_until': 30}},
    {'tick': 3, 'phase': 1, 'driver': 'fresh_certify_reserve_and_submit', 'attempt_id': 'attempt-current', 'idempotency_key': 'deploy-service-X-v2-episode-1', 'expected': ['One admissible deployment attempt may be accepted by the executor.', 'Goal remains outstanding.']},
    {'tick': 3, 'phase': 2, 'environment': 'drop_executor_ack', 'evaluator_only': True},
    {'tick': 4, 'phase': 0, 'driver': 'crash_restore_and_reconcile', 'expected': ['Reconcile the existing idempotency key.', 'No second external deployment effect is created.']},
    {'tick': 5, 'phase': 0, 'environment': 'deliver_unrelated_old_callback', 'public_payload': {'attempt_id': 'attempt-old', 'artifact_digest': 'sha256:v1-example', 'status': 'COMPLETED'}, 'expected': ['Do not attribute this callback to attempt-current.', 'No exact-product or durable goal relief for the current goal.']},
    {'tick': 6, 'phase': 0, 'environment': 'deliver_current_completion', 'public_payload': {'attempt_id': 'attempt-current', 'artifact_digest': 'sha256:v2-example', 'status': 'COMPLETED'}, 'expected': ['Exact product completion may be recorded.', 'Durable health is not yet established.']},
    {'tick': 7, 'phase': 0, 'environment': 'deliver_health_sample', 'public_payload': {'service': 'service-X', 'artifact_digest': 'sha256:v2-example', 'healthy': True, 'sample_tick': 7}},
    {'tick': 8, 'phase': 0, 'environment': 'withhold_required_health_sample', 'expected': ['No continuous or consecutive-observation success may be inferred from the missing sample.']},
    {'tick': 9, 'phase': 0, 'environment': 'deliver_health_sample', 'public_payload': {'service': 'service-X', 'artifact_digest': 'sha256:v2-example', 'healthy': False, 'sample_tick': 9}},
    {'tick': 10, 'phase': 0, 'environment': 'deliver_health_sample', 'public_payload': {'service': 'service-X', 'artifact_digest': 'sha256:v2-example', 'healthy': True, 'sample_tick': 10}},
    {'tick': 11, 'phase': 0, 'environment': 'deliver_health_sample', 'public_payload': {'service': 'service-X', 'artifact_digest': 'sha256:v2-example', 'healthy': True, 'sample_tick': 11}},
    {'tick': 12, 'phase': 0, 'environment': 'deliver_health_sample', 'public_payload': {'service': 'service-X', 'artifact_digest': 'sha256:v2-example', 'healthy': True, 'sample_tick': 12}, 'expected': ['Three consecutive required ticks now establish the declared observation-based durability predicate.', 'Goal can be discharged with these exact supports.']},
]
write_json('deployment_episode.example.json', {
    'schema': 'rd-validation-design/0.1',
    'status': 'ILLUSTRATIVE_FIXTURE_NOT_EXECUTABLE_ENVIRONMENT',
    'case_id': 'deployment-revocation-restart-wrong-product-001',
    'mode': 'conformance',
    'public_initial_state': {
        'context_id': 'service-X-production',
        'logical_tick': 0,
        'knowledge_revision': 1,
        'policy_revision': 1,
        'artifact_digest': 'sha256:v2-example',
        'test_status': 'UNKNOWN',
        'credential': {'id': 'credential-A', 'revision': 1, 'valid': True, 'valid_until': 30},
        'deployment_slots': 1,
        'deployment_requirement': ['test_exact_artifact_passes', 'current_credential_valid_at_dispatch', 'slot_reserved', 'current_policy_passes'],
        'executor_contract': {'idempotent_submission': True, 'authoritative_status_lookup': True},
        'goal': {
            'goal_id': 'goal-1',
            'target': 'service-X healthy on sha256:v2-example',
            'initial_loss': 1,
            'completion': {'consecutive_healthy_samples': 3, 'required_sample_interval_ticks': 1, 'max_arrival_lag_ticks': 0, 'exact_artifact_required': True},
            'scope_note': 'Three consecutive specified observations; not a proof of continuous unobserved health.'
        },
    },
    'evaluator_only': {
        'families': ['F01', 'F08', 'F09', 'F10', 'F12', 'F16'],
        'script': events,
        'assertion_format': 'human-readable contract statements, not executable code',
        'earliest_supported_goal_discharge_tick': 12,
        'future_script_visible_to_agent': False,
        'unexpected_actions': 'log and judge against the same public admission contract',
    },
})
inputs = {}
for name in ['reachability_atomspace_specification.md', 'pressure_field_pln_lifecycle_integration.md', 'pressure_field_lifecycle_reference_checks.py']:
    path = HERE.parent / name
    inputs[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
write_json('manifest.json', {
    'package': 'reachability_validation_design',
    'version': '0.1',
    'date': '2026-09-30',
    'status': 'PROPOSAL_AND_ILLUSTRATIVE_CONTRACTS',
    'input_artifacts': inputs,
    'contains_experimental_results': False,
    'contains_actual_implementation_adapter': False,
    'example_files': ['ablation_manifest.example.json', 'deployment_episode.example.json'],
})
