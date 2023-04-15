from functools import partial
from staketaxcsv.algo.api_algoindexer import AlgoIndexerAPI
from staketaxcsv.algo.asset import Algo
from staketaxcsv.algo.dapp import Dapp
from staketaxcsv.algo.export_tx import (
    export_borrow_tx,
    export_deposit_collateral_tx,
    export_repay_tx,
    export_reward_tx,
    export_spend_fee_tx,
    export_swap_tx,
    export_unknown,
    export_withdraw_collateral_tx,
)
from staketaxcsv.algo.transaction import (
    get_fee_amount,
    get_inner_transfer_asset,
    get_transaction_note,
    get_transfer_asset,
    is_app_call,
    is_asset_optin,
    is_transaction_sender,
    is_transfer,
    is_transfer_receiver
)
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.common.TxInfo import TxInfo

# For reference
# https://github.com/Folks-Finance/folks-finance-js-sdk
# https://docs.folks.finance/developer/contracts

APPLICATION_ID_FOLKSV2_POOL_MANAGER = 971350278
APPLICATION_ID_FOLKSV2_DEPOSIT = 971353536
APPLICATION_ID_FOLKSV2_LOANS = [
    971388781,  # General
    971388977,  # Stablecoin Efficiency
    971389489,  # ALGO Efficiency
]
APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER = 971333964
APPLICATION_ID_FOLKSV2_OP_UP = 971335937  # Oracle Price Update?

APPLICATION_ID_FOLKSV2_POOLS = [
    971368268,   # ALGO
    971370097,   # gALGO
    971372237,   # USDC
    971372700,   # USDt
    971373361,   # goBTC
    971373611,   # goETH
    1044267181,  # OPUL
]
APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR = [
    991196662,   # Distributor G6
    1073098885,  # Distributor G7
]

NOTE_FOLKSV2_DEPOSIT_APP = "da"
NOTE_FOLKSV2_LOAN_APP = "la"
NOTE_FOLKSV2_LOAN_NAME = "ff-name"

FOLKSV2_TRANSACTION_DEPOSIT_ESCROW_OPTIN = "sx8Gbg=="       # "opt_escrow_into_asset" ABI selector
FOLKSV2_TRANSACTION_DEPOSIT = "udVC+w=="                    # "deposit" ABI selector
FOLKSV2_TRANSACTION_DEPOSIT_WITHDRAW = "ruOUyw=="           # "withdraw" ABI selector
FOLKSV2_TRANSACTION_FLASH_LOAN_BEGIN = "JGiTsw=="           # "flash_loan_begin" ABI selector
FOLKSV2_TRANSACTION_FLASH_LOAN_END = "Kgiw7Q=="             # "flash_loan_end" ABI selector
FOLKSV2_TRANSACTION_LOAN_ADD_COLLATERAL = "aV6pHw=="        # "add_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_SYNC_COLLATERAL = "YLBwBQ=="       # "sync_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_BORROW = "l9QG5g=="                # "borrow" ABI selector
FOLKSV2_TRANSACTION_LOAN_REPAY_WITH_TXN = "o8ijmA=="        # "repay_with_txn" ABI selector
FOLKSV2_TRANSACTION_LOAN_REDUCE_COLLATERAL = "kXRHtw=="     # "reduce_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_REMOVE_COLLATERAL = "Iq24qQ=="     # "remove_collateral" ABI selector
FOLKSV2_TRANSACTION_LOAN_REMOVE_LOAN = "UL3+hg=="           # "remove_loan" ABI selector
FOLKSV2_TRANSACTION_LOAN_SWAP_BEGIN = "GIPo0w=="            # "swap_collateral_begin" ABI selector
FOLKSV2_TRANSACTION_LOAN_SWAP_END = "SBn0/w=="              # "swap_collateral_end" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE = "wZh8Kw=="                 # "governance" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_MINT = "1MGHdQ=="            # "mint" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_BURN = "ojqoeg=="            # "burn" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_GALGO_MINT = "bh9UTw=="      # v1 galgo "mint" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_UNMINT_PREMINT = "n1wNEA=="  # "unmint_premint" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_CLAIM_PREMINT = "kZDyNg=="   # "claim_premint" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_UNMINT = "3c0QwA=="          # "mint" ABI selector
FOLKSV2_TRANSACTION_GOVERNANCE_REWARDS_CLAIM = "2wMoWg=="   # "claim_rewards" ABI selector

APPLICATION_ID_DEFLEX_ORDER_ROUTER = 989365103
DEFLEX_TRANSACTION_SWAP_FINALIZE = "tTD7Hw=="  # "User_swap_finalize" ABI selector


class FolksV2(Dapp):
    def __init__(self, indexer: AlgoIndexerAPI, user_address: str, account: dict, exporter: Exporter) -> None:
        super().__init__(indexer, user_address, account, exporter)
        self.indexer = indexer
        self.user_address = user_address
        self.exporter = exporter

    @property
    def name(self):
        return "Folks v2"

    def get_extra_transactions(self) -> list:
        return []

    def is_dapp_transaction(self, group: list) -> bool:
        return (self._is_folksv2_deposit(group)
                    or self._is_folksv2_withdraw(group)
                    or self._is_folksv2_create_loan(group)
                    or self._is_folksv2_move_to_collateral(group)
                    or self._is_folksv2_borrow(group)
                    or self._is_folksv2_repay_with_txn(group)
                    or self._is_folksv2_swap_repay(group)
                    or self._is_folksv2_swap_collateral(group)
                    or self._is_folksv2_increase_collateral(group)
                    or self._is_folksv2_reduce_collateral(group)
                    or self._is_folksv2_remove_loan(group)
                    or self._is_folksv2_governance_commit(group)
                    or self._is_folksv2_governance_burn(group)
                    or self._is_folksv2_governance_galgo_mint(group)
                    or self._is_folksv2_governance_unmint_premint(group)
                    or self._is_folksv2_governance_claim_premint(group)
                    or self._is_folksv2_governance_unmint(group)
                    or self._is_folksv2_governance_rewards_claim(group)
                    or self._is_folksv2_governance_leveraged_commit(group))

    def handle_dapp_transaction(self, group: list, txinfo: TxInfo):
        if self._is_folksv2_deposit(group):
            self._handle_folksv2_deposit(group, txinfo)

        elif self._is_folksv2_withdraw(group):
            self._handle_folksv2_withdraw(group, txinfo)

        elif self._is_folksv2_create_loan(group):
            pass

        elif self._is_folksv2_move_to_collateral(group):
            pass

        elif self._is_folksv2_borrow(group):
            self._handle_folksv2_borrow(group, txinfo)

        elif self._is_folksv2_repay_with_txn(group):
            self._handle_folksv2_repay_with_txn(group, txinfo)

        elif self._is_folksv2_swap_repay(group):
            self._handle_folksv2_swap_repay(group, txinfo)

        elif self._is_folksv2_swap_collateral(group):
            self._handle_folksv2_swap_collateral(group, txinfo)

        elif self._is_folksv2_increase_collateral(group):
            self._handle_folksv2_deposit(group[:-2], txinfo)

        elif self._is_folksv2_reduce_collateral(group):
            self._handle_folksv2_reduce_collateral(group, txinfo)

        elif self._is_folksv2_remove_loan(group):
            pass

        elif self._is_folksv2_governance_commit(group):
            self._handle_folksv2_governance_commit(group, txinfo)

        elif self._is_folksv2_governance_burn(group):
            self._handle_folksv2_governance_burn(group, txinfo)

        elif self._is_folksv2_governance_galgo_mint(group):
            self._handle_folksv2_governance_galgo_mint(group, txinfo)

        elif self._is_folksv2_governance_unmint_premint(group):
            self._handle_folksv2_governance_unmint_premint(group, txinfo)

        elif self._is_folksv2_governance_claim_premint(group):
            self._handle_folksv2_governance_claim_premint(group, txinfo)

        elif self._is_folksv2_governance_unmint(group):
            self._handle_folksv2_governance_unmint(group, txinfo)

        elif self._is_folksv2_governance_rewards_claim(group):
            self._handle_folksv2_governance_rewards_claim(group, txinfo)

        elif self._is_folksv2_governance_leveraged_commit(group):
            self._handle_folksv2_governance_leveraged_commit(group, txinfo)

        else:
            export_unknown(self.exporter, txinfo)

    def _is_folksv2_deposit(self, group):
        length = len(group)
        if length < 2 or length > 5:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_FOLKSV2_POOLS, FOLKSV2_TRANSACTION_DEPOSIT):
            return False

        if not is_transfer(group[-2]):
            return False

        return is_transaction_sender(self.user_address, group[-2])

    def _is_folksv2_withdraw(self, group):
        length = len(group)
        if length > 2:
            return False

        if length == 2 and not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
            return False

        return is_app_call(group[-1], APPLICATION_ID_FOLKSV2_DEPOSIT, FOLKSV2_TRANSACTION_DEPOSIT_WITHDRAW)

    def _is_folksv2_create_loan(self, group):
        if len(group) != 2:
            return False

        if not is_transfer(group[0]):
            return False

        if not is_transaction_sender(self.user_address, group[0]):
            return False

        note = get_transaction_note(group[0], len(NOTE_FOLKSV2_LOAN_NAME))
        if note != NOTE_FOLKSV2_LOAN_NAME:
            return False

        if not is_transfer(group[1]):
            return False

        if not is_transaction_sender(self.user_address, group[1]):
            return False

        note = get_transaction_note(group[1], len(NOTE_FOLKSV2_LOAN_APP))
        return note == NOTE_FOLKSV2_LOAN_APP

    def _is_folksv2_move_to_collateral(self, group):
        if len(group) != 6:
            return False

        if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
            return False

        if not is_transfer(group[1]):
            return False

        if not is_transaction_sender(self.user_address, group[1]):
            return False

        if not is_app_call(group[2], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_ADD_COLLATERAL):
            return False

        if not is_app_call(group[3], APPLICATION_ID_FOLKSV2_DEPOSIT, FOLKSV2_TRANSACTION_DEPOSIT_WITHDRAW):
            return False

        return is_app_call(group[5], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SYNC_COLLATERAL)

    def _is_folksv2_borrow(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_app_call(group[-2], APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER):
            return False

        return is_app_call(group[-1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_BORROW)

    def _is_folksv2_repay_with_txn(self, group):
        if len(group) != 2:
            return False

        if not is_transfer(group[0]):
            return False

        if not is_transaction_sender(self.user_address, group[0]):
            return False

        return is_app_call(group[1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REPAY_WITH_TXN)

    def _is_folksv2_increase_collateral(self, group):
        length = len(group)
        if length < 5 or length > 7:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SYNC_COLLATERAL):
            return False

        if not is_app_call(group[-2], APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER):
            return False

        return self._is_folksv2_deposit(group[:-2])

    def _is_folksv2_reduce_collateral(self, group):
        if len(group) != 3:
            return False

        if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
            return False

        if not is_app_call(group[1], APPLICATION_ID_FOLKSV2_ORACLE_ADAPTER):
            return False

        return is_app_call(group[2], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REDUCE_COLLATERAL)

    def _is_folksv2_remove_loan(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_app_call(group[-2], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_REMOVE_LOAN):
            return False

        return is_transfer(group[-1])

    def _is_folksv2_swap_collateral(self, group):
        length = len(group)
        if length < 10 or length > 12:
            return False

        if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_OP_UP):
            return False

        if not is_app_call(group[1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SWAP_BEGIN):
            return False

        if not is_transfer(group[2]):
            return False

        if not is_transaction_sender(self.user_address, group[2]):
            return False

        if not is_transfer(group[-6]):
            return False

        if not is_transaction_sender(self.user_address, group[-6]):
            return False

        if not is_app_call(group[-5], APPLICATION_ID_FOLKSV2_POOLS, FOLKSV2_TRANSACTION_DEPOSIT):
            return False

        return is_app_call(group[-1], APPLICATION_ID_FOLKSV2_LOANS, FOLKSV2_TRANSACTION_LOAN_SWAP_END)

    def _is_folksv2_swap_repay(self, group):
        if len(group) != 4:
            return False

        if not is_transfer(group[0]):
            return False

        if not is_transaction_sender(self.user_address, group[0]):
            return False

        if not is_app_call(group[1], APPLICATION_ID_DEFLEX_ORDER_ROUTER, DEFLEX_TRANSACTION_SWAP_FINALIZE):
            return False

        return self._is_folksv2_repay_with_txn(group[2:])

    def _is_folksv2_governance_commit(self, group):
        if len(group) != 5:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR, FOLKSV2_TRANSACTION_GOVERNANCE):
            return False

        if not is_app_call(group[-2], APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR, FOLKSV2_TRANSACTION_GOVERNANCE_MINT):
            return False

        if not is_transfer(group[-3]):
            return False

        return is_transaction_sender(self.user_address, group[-3])

    def _is_folksv2_governance_burn(self, group):
        if len(group) != 2:
            return False

        if not is_transfer(group[0]):
            return False

        if not is_transaction_sender(self.user_address, group[0]):
            return False

        return is_app_call(group[1], APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR, FOLKSV2_TRANSACTION_GOVERNANCE_BURN)

    def _is_folksv2_governance_galgo_mint(self, group):
        length = len(group)
        if length < 2 or length > 3:
            return False

        if not is_app_call(group[-1], APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR, FOLKSV2_TRANSACTION_GOVERNANCE_GALGO_MINT):
            return False

        if not is_transfer(group[-2]):
            return False

        return is_transaction_sender(self.user_address, group[-2])

    def _is_folksv2_governance_unmint_premint(self, group):
        if len(group) != 2:
            return False

        if not is_app_call(group[0],
                        APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR,
                        FOLKSV2_TRANSACTION_GOVERNANCE_UNMINT_PREMINT):
            return False

        return is_app_call(group[1], APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR, FOLKSV2_TRANSACTION_GOVERNANCE)

    def _is_folksv2_governance_claim_premint(self, group):
        if len(group) != 1:
            return False

        return is_app_call(group[0],
                        APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR,
                        FOLKSV2_TRANSACTION_GOVERNANCE_CLAIM_PREMINT)

    def _is_folksv2_governance_unmint(self, group):
        if len(group) != 2:
            return False

        if not is_transfer(group[0]):
            return False

        if not is_transaction_sender(self.user_address, group[0]):
            return False

        return is_app_call(group[1], APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR, FOLKSV2_TRANSACTION_GOVERNANCE_UNMINT)

    def _is_folksv2_governance_rewards_claim(self, group):
        if len(group) != 1:
            return False

        return is_app_call(group[0],
                        APPLICATION_ID_FOLKS_GOVERNANCE_DISTRIBUTOR,
                        FOLKSV2_TRANSACTION_GOVERNANCE_REWARDS_CLAIM)

    def _is_folksv2_governance_leveraged_commit(self, group):
        if len(group) != 14:
            return False

        if not is_app_call(group[0], APPLICATION_ID_FOLKSV2_POOLS, FOLKSV2_TRANSACTION_FLASH_LOAN_BEGIN):
            return False

        if not self._is_folksv2_create_loan(group[1:3]):
            return False

        if not self._is_folksv2_governance_galgo_mint(group[3:5]):
            return False

        if not self._is_folksv2_deposit(group[6:8]):
            return False

        if not self._is_folksv2_borrow(group[10:12]):
            return False

        if not is_transfer(group[-2]):
            return False

        if not is_transaction_sender(self.user_address, group[-2]):
            return False

        return is_app_call(group[-1], APPLICATION_ID_FOLKSV2_POOLS, FOLKSV2_TRANSACTION_FLASH_LOAN_END)

    def _handle_folksv2_deposit(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[-2])

        export_deposit_collateral_tx(self.exporter, txinfo, send_asset, fee_amount, self.name, z_index)

    def _handle_folksv2_withdraw(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[-1],
                                                filter=partial(is_transfer_receiver, self.user_address))

        # TODO track cost basis to calculate earnings
        export_withdraw_collateral_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name)

    def _handle_folksv2_borrow(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[-1],
                                                filter=partial(is_transfer_receiver, self.user_address))

        export_borrow_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name + " Borrow", z_index)

    def _handle_folksv2_repay_with_txn(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[0])
        receive_asset = get_inner_transfer_asset(group[1],
                                                filter=partial(is_transfer_receiver, self.user_address))
        if receive_asset is not None:
            send_asset -= receive_asset

        export_repay_tx(self.exporter, txinfo, send_asset, fee_amount, self.name + " Repay")

    def _handle_folksv2_reduce_collateral(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[2],
                                                filter=partial(is_transfer_receiver, self.user_address))

        # TODO track cost basis to calculate earnings
        export_withdraw_collateral_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name)

    def _handle_folksv2_swap_repay(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group[:2])

        send_asset = get_transfer_asset(group[0])
        receive_asset = get_inner_transfer_asset(group[1],
                                                filter=partial(is_transfer_receiver, self.user_address))

        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name, -1)
        self._handle_folksv2_repay_with_txn(group[2:], txinfo)

    def _handle_folksv2_swap_collateral(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[2])
        receive_asset = get_transfer_asset(group[-6])

        # TODO track cost basis to calculate earnings
        export_withdraw_collateral_tx(self.exporter, txinfo, send_asset, 0, self.name, 0)
        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name, 1)
        export_deposit_collateral_tx(self.exporter, txinfo, receive_asset, 0, self.name, 2)

    def _handle_folksv2_governance_commit(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[-3])
        export_deposit_collateral_tx(self.exporter, txinfo, send_asset, fee_amount, self.name)

    def _handle_folksv2_governance_burn(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[0])
        receive_asset = get_inner_transfer_asset(group[1])
        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)

    def _handle_folksv2_governance_galgo_mint(self, group, txinfo, z_index=0):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[-2])
        receive_asset = get_inner_transfer_asset(group[-1])
        if receive_asset is not None:
            export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name, z_index)

    def _handle_folksv2_governance_unmint_premint(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[0])
        export_withdraw_collateral_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name)

    def _handle_folksv2_governance_claim_premint(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[0])

        send_asset = Algo(receive_asset.uint_amount)
        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)

    def _handle_folksv2_governance_unmint(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        send_asset = get_transfer_asset(group[0])
        receive_asset = get_inner_transfer_asset(group[1])
        export_swap_tx(self.exporter, txinfo, send_asset, receive_asset, fee_amount, self.name)

    def _handle_folksv2_governance_rewards_claim(self, group, txinfo):
        fee_amount = get_fee_amount(self.user_address, group)

        receive_asset = get_inner_transfer_asset(group[0])
        export_reward_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name + " Governance")

    def _handle_folksv2_governance_leveraged_commit(self, group, txinfo):
        transaction = group[0]
        fee_amount = transaction["fee"]
        receive_asset = get_inner_transfer_asset(transaction)
        export_borrow_tx(self.exporter, txinfo, receive_asset, fee_amount, self.name + " Borrow", 0)

        self._handle_folksv2_governance_galgo_mint(group[3:5], txinfo, 1)
        self._handle_folksv2_deposit(group[6:8], txinfo, 2)
        self._handle_folksv2_borrow(group[10:12], txinfo, 3)

        transaction = group[-1]
        fee_amount = transaction["fee"]
        transaction = group[-2]
        send_asset = get_transfer_asset(transaction)
        export_repay_tx(self.exporter, txinfo, send_asset, fee_amount, self.name + " Repay", 4)
