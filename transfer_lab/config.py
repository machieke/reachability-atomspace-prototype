from .cases import configuration as old_configuration,PARENTS
ARMS=('TRANSFER-scan','TRANSFER-native')
def configuration():return dict(old_configuration(),retrieval_arms=list(ARMS),modes=['native'],parents=list(PARENTS),order='manifest parents; scan first on even indexes, native first on odd indexes',repetitions=1)
def cells():
    for i,parent in enumerate(PARENTS):
        for arm in ARMS if i%2==0 else reversed(ARMS):yield 0,arm,'native',parent
# Keep the existing artifact naming convention; sweep=0 denotes the sole pass.
def folder(sweep,arm,mode,parent):return f's{sweep}-{arm}-{mode}-{parent}'
