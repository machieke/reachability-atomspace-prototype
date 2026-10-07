"""Unchanged task configuration plus preregistered retrieval factors."""
from multihop_lab.cases import configuration as original
from experimental_native_recall.schema import QueryLimits
ARMS=('MH-scan','MH-native')
def configuration():
    return dict(original(),retrieval_arms=list(ARMS),query_limits=QueryLimits().__dict__,retrieval_protocol='native-multihop/v1')
