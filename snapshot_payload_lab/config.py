"""Exactly two predeclared within-group counterbalanced sweeps."""
from native_multihop_lab.config import configuration as original
from multihop_lab.cases import PARENTS
ARMS=('MH-scan','MH-native-session-full','MH-native-session-compact')
def configuration():
    return dict(original(),retrieval_arms=list(ARMS),sweeps=[0,1],runtime_protocol='sealed-runtime-generation/v1',projection_schemas=['native-atomspace-recall/v1','native-atomspace-recall-compact/v1'],order='sweep, formula mode, parent, arms forward in sweep 0 / reverse in sweep 1')
def cells():
    for sweep in (0,1):
        for mode in configuration()['modes']:
            for parent in PARENTS:
                for arm in ARMS if sweep==0 else reversed(ARMS):yield sweep,arm,mode,parent
def folder(sweep,arm,mode,parent):return f's{sweep}-{arm}-{mode}-{parent}'
