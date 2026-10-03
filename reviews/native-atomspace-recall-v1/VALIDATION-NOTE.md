# Full-suite discovery correction

All implementation, comparator, test and auditor sources stayed frozen at
`79f4f439a510cfb6c94a831985e8daee1cfbd84e`. No historical test was edited.

The initial full default run used `unittest.defaultTestLoader.discover('tests',
pattern='test_*.py')`, equivalent to the repository README's `-s tests` discovery
convention. It completed all 1,006 tests in 1,286.092 seconds: 1,005 passed, one
failed, and none errored or skipped. The retained failure was
`test_goal_pln.GoalPLNTests.test_four_mutation_witnesses`.

The pre-existing test patches `tests.test_goal_pln.closure`. Unqualified discovery
loads the executing test as `test_goal_pln`, so the patch targets a second module
instance and the intended mutation is not installed in the executing test. Its
`assertRaises(AssertionError)` therefore fails. This is a discovery/mock-target
interaction, not evidence that an installed mutation escaped the checker.

The same frozen test passes when invoked by its package-qualified name:

```sh
uv run --no-project python -m unittest tests.test_goal_pln.GoalPLNTests.test_four_mutation_witnesses -v
```

To verify the entire suite under that convention, a second full run uses
`discover('tests', pattern='test_*.py', top_level_dir='.')`, equivalent to:

```sh
uv run --no-project python -m unittest discover -s tests -t . -v
```

The package-qualified full run passed all 1,006 tests in 1242.175 seconds, with no failures, errors or skips. Its complete inventory matches the first run after removing only the `tests.` prefix. Both source/test hash inventories match, and end-of-run checks confirm they stayed unchanged.

The archive retains both runner scripts, start-time source/test hashes and complete
inventories, both full-suite logs/results, and the one-test diagnostic log. The
comparison, native integration suite and numerical checks were not repeated or
reclassified. The original failure is preserved; it is not reported as a pass.
