"""Independent small finite transport checks; no native binary required."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from pathlib import Path
import ast,random,unittest
from experimental_attention.field import Field,Arc,StaleField
from experimental_attention.workspace import Workspace,Caps,Bound


def dense_reference(values,arcs,binding='b',context='ctx'):
    keys=sorted(values);q=[[Fraction(0) for _ in keys] for _ in keys]
    for a in arcs:
        if a.status=='PASS' and a.binding==binding and a.context==context and a.source!=a.target:
            q[keys.index(a.source)][keys.index(a.target)]+=Fraction(a.rate)
    totals=[sum(row) for row in q];maximum=max(totals,default=0)
    dt=Fraction(9,10)/maximum if maximum else 0
    matrix=[[dt*q[i][j] if i!=j else 1-dt*totals[i] for j in range(len(keys))] for i in range(len(keys))]
    return {keys[j]:float(sum(Fraction(values[keys[i]])*matrix[i][j] for i in range(len(keys)))) for j in range(len(keys))}


class AttentionFieldTests(unittest.TestCase):
    def test_independent_generated_direction_masks_conservation(self):
        rng=random.Random(0)
        for count in range(2,7):
            for repeat in range(16):
                field=Field('b','ctx');keys=[str(i) for i in range(count)]
                for k in keys:field.add(k)
                field.seed(keys[:2]);arcs=[Arc(a,b,'inspect','ctx','b',rng.choice(('PASS','FAIL','UNKNOWN','STALE')),'test') for a,b in product(keys,repeat=2) if a!=b]
                before=dict(field.activation);expected=dense_reference(before,arcs)
                event=field.step(arcs,lambda:'b')
                for k in keys:self.assertAlmostEqual(field.activation[k],expected[k],places=14)
                self.assertTrue(all(v>=0 for v in field.activation.values()));self.assertLess(abs(event['residual']),1e-12)
    def test_direction_and_all_closed_identity(self):
        f=Field('b','ctx');f.add('a');f.add('b');f.seed(['a'])
        a=Arc('a','b','inspect','ctx','b','FAIL','blocked',float('nan'));old=dict(f.activation)
        f.step([a],lambda:'b');self.assertEqual(old,f.activation)
        f.step([replace(a,status='PASS',rate=1)],lambda:'b');self.assertAlmostEqual(f.activation['b'],.72)
        self.assertLess(f.activation['a'],.1)
    def test_M12_gate_before_arithmetic_mutation_witness(self):
        class Explosive:
            def __float__(self):raise OverflowError('closed rate must never be touched')
        arc=Arc('a','b','inspect','ctx','b','FAIL','closed',Explosive());f=Field('b','ctx')
        f.add('a');f.add('b');f.seed(['a']);f.step([arc],lambda:'b')
        # Deliberately mutated ordering evaluates the forbidden payload first.
        def mutant(a):return float(a.rate)*(a.status=='PASS')
        with self.assertRaises(OverflowError):mutant(arc)
        with self.assertRaises(ValueError):f.step([replace(arc,status='PASS',rate=float('nan'))],lambda:'b')
    def test_seed_duplicate_paths_growth_cooling_and_eviction(self):
        f=Field('b','ctx');f.add('a');self.assertEqual(f.seed(['a','a']),.8)
        before=(dict(f.activation),f.reservoir);self.assertEqual(f.seed(['a']),0);self.assertEqual(before,(f.activation,f.reservoir))
        f.add('new');self.assertEqual(f.activation['new'],0)
        f.cool();self.assertAlmostEqual(f.activation['a'],.76);self.assertAlmostEqual(f.reservoir,.24)
        f.remove('a');self.assertAlmostEqual(f.reservoir,1);self.assertEqual(f.activation,{'new':0})
    def test_stale_step_cancels_publication_and_context_closes(self):
        f=Field('b','ctx');f.add('a');f.add('b');f.seed(['a']);a=Arc('a','b','inspect','ctx','b','PASS','read')
        old=(dict(f.activation),f.reservoir,f.epoch);answers=iter(('b','new'))
        with self.assertRaises(StaleField):f.step([a],lambda:next(answers))
        self.assertEqual(old,(f.activation,f.reservoir,f.epoch))
        f.step([replace(a,context='other',rate=float('nan'))],lambda:'b');self.assertEqual(old[0],f.activation)
    def test_generated_relabel_order_invariance(self):
        rng=random.Random(12)
        for n in range(2,8):
            base=Field('b','ctx');renamed=Field('b','ctx');names=[str(i) for i in range(n)];permutation=names[:];rng.shuffle(permutation);mapping=dict(zip(names,permutation))
            for k in names:base.add(k);renamed.add(mapping[k])
            base.seed(names[:1]);renamed.seed([mapping[names[0]]])
            arcs=[Arc(str(i),str(i+1),'premise','ctx','b','PASS','read') for i in range(n-1)]
            transformed=[replace(a,source=mapping[a.source],target=mapping[a.target]) for a in reversed(arcs)]
            for _ in range(4):base.step(arcs,lambda:'b');renamed.step(transformed,lambda:'b')
            for k in names:self.assertAlmostEqual(base.activation[k],renamed.activation[mapping[k]],places=14)
    def test_lru_pins_overflow_and_mass_return(self):
        w=Workspace('b','ctx',Caps(active=3));w.control('control',{'needed':True});w.admit('a',1,anchor=True);w.field.seed(['a']);w.admit('b',2)
        w.get('a');w.admit('c',3);self.assertNotIn('b',w.entries);self.assertIn('control',w.entries)
        w.admit('d',4);self.assertNotIn('a',w.entries);self.assertAlmostEqual(w.field.reservoir,1)
        with self.assertRaisesRegex(Bound,'INDIVISIBLE'):w.pin_bundle([(str(i),i) for i in range(4)])
        w.pin_bundle([('c',3),('d',4)])
        with self.assertRaisesRegex(Bound,'ALL_PINNED'):w.admit('z',5)
        w.release();w.admit('z',5);self.assertIn('control',w.entries)
    def test_byte_and_control_bounds_and_no_evaluator_import(self):
        w=Workspace('b','ctx',Caps(active_bytes=8))
        with self.assertRaises(Bound):w.admit('large','x'*9)
        self.assertFalse(w.entries)
        w=Workspace('b','ctx',Caps(controls=0))
        with self.assertRaisesRegex(Bound,'CONTROL'):w.control('one',{})
        for p in Path('experimental_attention').glob('*.py'):
            for n in ast.walk(ast.parse(p.read_text())):
                modules=[n.module or ''] if isinstance(n,ast.ImportFrom) else [a.name for a in n.names] if isinstance(n,ast.Import) else []
                self.assertFalse(any(m.startswith(('attention_lab','goal_pln_lab','validation_lab')) for m in modules))
