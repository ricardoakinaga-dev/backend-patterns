import copy
import runpy
import unittest


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = runpy.run_path("scripts/run-context-efficiency.py")
        cls.scenarios = cls.module["load_scenarios"]()

    def test_route_ignores_evaluator_only_fields(self):
        scenario = copy.deepcopy(self.scenarios[0])
        baseline = self.module["route"](scenario)
        scenario.update({
            "family": "mutated",
            "split": "holdout",
            "expected_decision": "gold leakage",
            "recommended_references": ["references/security-boundaries.md"],
            "routing_relevance": {"mutated": "gold"},
        })
        self.assertEqual(baseline, self.module["route"](scenario))

    def test_effect_bundle_mutation_changes_a_public_route(self):
        changed = []
        for scenario in self.scenarios:
            before = self.module["route"](scenario)
            after = self.module["route_with_trace"](scenario, {"atomic-effect-boundary"})["references"]
            if before != after:
                changed.append(scenario["id"])
        self.assertTrue(changed)

    def test_routes_only_reference_package_files(self):
        package_refs = {path.name for path in self.module["ROOT"].joinpath("references").glob("*.md")}
        for scenario in self.scenarios:
            self.assertTrue(set(self.module["route"](scenario)).issubset(package_refs))

    def test_context_growth_bound_rejects_load_all_mutant(self):
        globals_dict = self.module["run"].__globals__
        original = globals_dict["_context_bytes"]
        globals_dict["_context_bytes"] = lambda _loaded: 10_000_000
        try:
            report = self.module["run"]()
        finally:
            globals_dict["_context_bytes"] = original
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["context_growth_within_bound"])


if __name__ == "__main__":
    unittest.main()
