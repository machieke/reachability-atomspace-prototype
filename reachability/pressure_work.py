"""Common bounded public inference/observation frontier for B0 and B3."""
from heapq import heappop, heappush

from .admission_protocol import AdmissionInitial, literal
from .b0 import Candidate, Frontier
from .pressure import Edge, Node, Source, finite
from .trace_protocol import canonical, fingerprint


def check_condition(condition, atoms):
    pending, visited = [(condition, 0)], 0
    while pending:
        node, depth = pending.pop(); visited += 1
        if depth > 8 or visited > 128:
            raise ValueError('condition graph bound exceeded')
        if type(node) is int:
            literal(node, atoms)
        elif (type(node) is dict and len(node) == 1 and next(iter(node)) in ('AND', 'OR')
              and type(next(iter(node.values()))) is list and 1 <= len(next(iter(node.values()))) <= 8):
            pending.extend((child, depth+1) for child in next(iter(node.values())))
        else:
            raise ValueError('only finite FACT/AND/OR conditions are supported')


def holds(condition, facts):
    if type(condition) is int:
        return condition in facts
    operator, children = next(iter(condition.items()))
    return (all if operator == 'AND' else any)(holds(child, facts) for child in children)


def validate_public(public):
    if set(public) != {'schema', 'admission', 'context_id', 'clauses', 'costs', 'probes', 'goals', 'priorities'} or public['schema'] != 'pressure-work-public/v1':
        raise ValueError('unsupported reasoning work profile')
    initial = AdmissionInitial.parse(public['admission'])
    atoms = len(initial.atoms)
    from .admission_protocol import clauses
    clauses(public['clauses'], atoms)
    if not public['context_id'] or len(public['probes']) > 8 or not 1 <= len(public['goals']) <= 4:
        raise ValueError('public profile exceeds finite scope')
    rules = initial.wire()['rules']
    if set(public['costs']) != {r['rule_id'] for r in rules}:
        raise ValueError('exact declared rule costs required')
    for cost in public['costs'].values():
        if finite(cost, 100) < 1:
            raise ValueError('operation cost must be positive')
    if len({p['probe_id'] for p in public['probes']}) != len(public['probes']):
        raise ValueError('duplicate observation capability')
    for probe in public['probes']:
        if set(probe) != {'probe_id', 'literal', 'cost'} or not probe['probe_id'] or finite(probe['cost'], 100) < 1:
            raise ValueError('invalid observation capability')
        literal(probe['literal'], atoms)
    if len({g['goal_id'] for g in public['goals']}) != len(public['goals']):
        raise ValueError('duplicate goal')
    if len({g['source_id'] for g in public['goals']}) != len(public['goals']):
        raise ValueError('duplicate scoped demand source')
    if set(public['priorities']) != {g['goal_id'] for g in public['goals']}:
        raise ValueError('explicit priorities required for every goal')
    for goal in public['goals']:
        if set(goal) != {'goal_id', 'source_id', 'unit', 'loss', 'condition'} or not goal['unit']:
            raise ValueError('invalid goal contract')
        if type(goal['loss']) is not int or not 1 <= goal['loss'] <= 1000:
            raise ValueError('bounded integer goal loss required')
        check_condition(goal['condition'], atoms)
        policy = public['priorities'][goal['goal_id']]
        Source(public['context_id'], goal['source_id'], 'result', goal['goal_id'], goal['unit'],
            policy['unit'], policy['revision'], '', '', goal['loss'], 0,
            policy['weight'], policy['urgency'], policy['commitment'])
    return public


def current(snapshot):
    return {s['literal'] for s in snapshot['supports']}


def joint_status(snapshot, extra=()):
    from .logic import check_consistency
    from .model import Clause, Literal, Statement
    def typed(value):
        return Literal(Statement('candidate:atom', (str(abs(value)),)), value > 0)
    return check_consistency(tuple(Clause(tuple(map(typed, c))) for c in snapshot['clauses']),
        tuple(map(typed, sorted(current(snapshot) | set(extra)))), max_variables=8).status.value


def enumerate_work(public, snapshot, *, visit_limit=4096):
    """Same actual ready frontier for either controller, without evaluator data.

    Each inference binds a whole AND premise bundle, including exact support
    aliases. Probes are capabilities, not promised answers. No partial frontier
    is selected when discovery reaches its bound.
    """
    if snapshot['public_digest'] != fingerprint(public) or len(snapshot['supports']) > 128:
        raise ValueError('snapshot is outside the declared profile')
    visits, candidates = 0, []
    facts = current(snapshot)
    def visit():
        nonlocal visits
        visits += 1
        return visits <= visit_limit
    def add(kind, args, cost=0):
        candidates.append(Candidate(kind, tuple(sorted(args.items())), 1, cost))
    for rule in snapshot['rules']:
        if not visit():
            return Frontier((), visit_limit, False, False)
        if rule['conclusion'] in facts or not set(rule['premises']) <= facts:
            continue
        if joint_status(snapshot, (rule['conclusion'],)) != 'PASS':
            continue  # Shared, pure early rejection; execution still certifies.
        parents = []
        for premise in rule['premises']:
            choices = [s for s in snapshot['supports'] if s['literal'] == premise]
            chosen = min(choices, key=lambda s: (-(s['valid_until'] if s['valid_until'] is not None else 1000000), s['reference']))
            parents.append(chosen['reference'])
        add('derive', dict(rule_id=rule['rule_id'], rule_revision=rule['revision'], premises=canonical(parents)))
    for probe in public['probes']:
        if not visit():
            return Frontier((), visit_limit, False, False)
        if probe['literal'] not in facts:
            add('observe', dict(probe_id=probe['probe_id']), probe['cost'])
    for goal in snapshot['goals']:
        if not visit():
            return Frontier((), visit_limit, False, False)
        if goal['outstanding'] and (goal['condition_status'] == 'PASS' or goal['coverage']):
            add('monitor', dict(goal_id=goal['goal_id']), 1)
    return Frontier(tuple(sorted(candidates, key=lambda c: c.candidate_id)), visits, True,
                    all(g['outstanding'] == 0 for g in snapshot['goals']))


def operation_cost(public, candidate):
    return public['costs'][dict(candidate.arguments)['rule_id']] if candidate.kind == 'derive' else candidate.observation_cost


def anchor(candidate):
    args = dict(candidate.arguments)
    return {'derive': 'rule:', 'observe': 'probe:', 'monitor': 'monitor:'}[candidate.kind]+args[
        {'derive': 'rule_id', 'observe': 'probe_id', 'monitor': 'goal_id'}[candidate.kind]]


def build_graph(public, snapshot):
    """Build typed hypernodes from the detached authoritative goal/support view."""
    facts = current(snapshot)
    nodes, edges, sources = {}, [], []
    def node(name, operator, channel='infer', satisfied=False, blocked=None):
        nodes[name] = Node(name, operator, channel, satisfied, blocked)
        return name
    def edge(parent, child, kind, weight=1.):
        edges.append(Edge(parent, child, kind, weight))
    literals = set(range(1, len(public['admission']['atoms'])+1))
    literals |= {-x for x in literals}
    for value in sorted(literals):
        node('fact:'+str(value), 'OR', satisfied=value in facts)
    for rule in snapshot['rules']:
        ready = set(rule['premises']) <= facts
        permitted = joint_status(snapshot, (rule['conclusion'],))
        blocked = ('FORBIDDEN_ACTION' if permitted == 'FAIL' else 'UNKNOWN_OR_STALE_CHECK') if permitted != 'PASS' else (
            None if ready else 'UNMET_REQUIREMENTS')
        name = node('rule:'+rule['rule_id'], 'LEAF' if ready else 'AND', blocked=blocked)
        edge('fact:'+str(rule['conclusion']), name, 'epistemic', 1/public['costs'][rule['rule_id']])
        if not ready:
            for premise in sorted(set(rule['premises'])):
                edge(name, 'fact:'+str(premise), 'epistemic')
    for probe in public['probes']:
        name = node('probe:'+probe['probe_id'], 'LEAF', 'observe')
        edge('fact:'+str(probe['literal']), name, 'observation', 1/probe['cost'])
    parents = {e.parent for e in edges}
    for value in sorted(literals):
        name = 'fact:'+str(value)
        if name not in parents and value not in facts:
            node(name, 'LEAF', blocked='MISSING_CAPABILITY')
    def requirement(condition):
        if type(condition) is int:
            return 'fact:'+str(condition)
        operator, children = next(iter(condition.items()))
        name = node('requirement:'+fingerprint(condition), operator, satisfied=holds(condition, facts))
        for child in children:
            edge(name, requirement(child), 'lifecycle')
        return name
    for goal in snapshot['goals']:
        root = node('goal:'+goal['goal_id'], 'AND')
        monitor = node('monitor:'+goal['goal_id'], 'LEAF', 'observe')
        if goal['condition_status'] == 'PASS':
            edge(root, monitor, 'observation')
        else:
            edge(root, requirement(goal['condition']), 'teleological')
        policy = public['priorities'][goal['goal_id']]
        sources.append(Source(public['context_id'], goal['source_id'], goal['slice_id'], goal['goal_id'],
            goal['unit'], policy['unit'], policy['revision'], root, monitor, goal['outstanding'], goal['coverage'],
            policy['weight'], policy['urgency'], policy['commitment'], tuple(goal['relief_events'])))
    return list(nodes.values()), edges, sources


def b0_ranking(public, snapshot, candidates, *, state_limit=16384):
    """Best-first conditional plans over the public finite fact state space.

    Positive probe outcomes are possibilities, not oracle answers. All rule
    premises must be jointly present, clauses remain hard constraints, and shared
    prerequisites are paid for once in a plan. Rank weighted unresolved value per
    minimum declared remaining work; recompute after every actual observation.
    This is an optimistic scheduling heuristic, not a success probability.
    """
    from .logic import check_consistency
    from .model import Clause, Literal, Statement, Status
    def typed(value):
        return Literal(Statement('candidate:atom', (str(abs(value)),)), value > 0)
    constraints = tuple(Clause(tuple(map(typed, clause))) for clause in snapshot['clauses'])
    rules = snapshot['rules']
    options = [(tuple(r['premises']), r['conclusion'], public['costs'][r['rule_id']]) for r in rules]
    options += [((), p['literal'], p['cost']) for p in public['probes']]
    work = dict(states=0, transitions=0, joint_checks=0)
    ranks = {}
    for candidate in candidates:
        args = dict(candidate.arguments)
        facts = current(snapshot)
        if candidate.kind == 'derive':
            facts.add(next(r['conclusion'] for r in rules if r['rule_id'] == args['rule_id']))
        elif candidate.kind == 'observe':
            facts.add(next(p['literal'] for p in public['probes'] if p['probe_id'] == args['probe_id']))
        queue = [(operation_cost(public, candidate), tuple(sorted(facts)))]
        visited, found = set(), {}
        while queue:
            if work['states'] >= state_limit:
                return {}, work, False
            cost, ordered = heappop(queue)
            work['states'] += 1
            if ordered in visited:
                continue
            visited.add(ordered)
            state = set(ordered)
            work['joint_checks'] += 1
            if check_consistency(constraints, tuple(map(typed, ordered)), max_variables=8).status is not Status.PASS:
                continue
            for goal in snapshot['goals']:
                if goal['outstanding'] and holds(goal['condition'], state):
                    monitor_cost = 0 if candidate.kind == 'monitor' and args['goal_id'] == goal['goal_id'] else 1
                    found.setdefault(goal['goal_id'], cost+monitor_cost)
            if len(found) == sum(g['outstanding'] > 0 for g in snapshot['goals']):
                break
            for premises, conclusion, charge in options:
                work['transitions'] += 1
                if conclusion not in state and set(premises) <= state:
                    heappush(queue, (cost+charge, tuple(sorted(state | {conclusion}))))
        values = []
        for goal in snapshot['goals']:
            policy = public['priorities'][goal['goal_id']]
            benefit = goal['outstanding']*policy['weight']*policy['urgency']*policy['commitment']
            if goal['goal_id'] in found:
                values.append(benefit/found[goal['goal_id']])
        ranks[candidate.candidate_id] = (-max(values, default=0.), operation_cost(public, candidate), candidate.rank)
    return ranks, work, True
