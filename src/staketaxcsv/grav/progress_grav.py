from staketaxcsv.grav.config_grav import localconfig
from staketaxcsv.common.ibc.progress_rpc_nodes import ProgressRpc

SECONDS_PER_PAGE = 4
SECONDS_PER_TX = 0.4


class ProgressGrav(ProgressRpc):

    def __init__(self):
        super().__init__(localconfig, SECONDS_PER_PAGE, SECONDS_PER_TX)
