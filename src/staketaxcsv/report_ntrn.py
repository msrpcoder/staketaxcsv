"""
usage: python3 staketaxcsv/report_ntrn.py <walletaddress> [--format all|cointracking|koinly|..]

Prints transactions and writes CSV(s) to _reports/NTRN*.csv
"""

import logging

import staketaxcsv.ntrn.processor
from staketaxcsv.common.ibc import api_lcd, historical_balances
from staketaxcsv.ntrn.config_ntrn import localconfig
from staketaxcsv.common import report_util
from staketaxcsv.common.Cache import Cache
from staketaxcsv.common.Exporter import Exporter
from staketaxcsv.settings_csv import NTRN_NODE, TICKER_NTRN, MINTSCAN_ON
from staketaxcsv.common.ibc.tx_data import TxDataMintscan, TxDataLcd
from staketaxcsv.common.ibc.progress_mintscan import ProgressMintScan, SECONDS_PER_PAGE
from staketaxcsv.common.ibc.decorators import set_ibc_cache


def main():
    report_util.main_default(TICKER_NTRN)


def read_options(options):
    report_util.read_common_options(localconfig, options)
    localconfig.start_date = options.get("start_date", None)
    localconfig.end_date = options.get("end_date", None)
    logging.info("localconfig: %s", localconfig.__dict__)


def _txdata():
    max_txs = localconfig.limit
    return TxDataMintscan(TICKER_NTRN, max_txs) if MINTSCAN_ON else TxDataLcd(NTRN_NODE, max_txs)


def wallet_exists(wallet_address):
    return api_lcd.make_lcd_api(NTRN_NODE).account_exists(wallet_address)


def txone(wallet_address, txid):
    elem = _txdata().get_tx(txid)

    exporter = Exporter(wallet_address, localconfig, TICKER_NTRN)
    txinfo = staketaxcsv.ntrn.processor.process_tx(wallet_address, elem, exporter)

    if localconfig.debug:
        txinfo.print()

    return exporter


def estimate_duration(wallet_address):
    start_date, end_date = localconfig.start_date, localconfig.end_date
    return SECONDS_PER_PAGE * _txdata().get_txs_pages_count(wallet_address, start_date, end_date)


@set_ibc_cache()
def txhistory(wallet_address):
    """ Configure localconfig based on options dictionary. """
    start_date, end_date = localconfig.start_date, localconfig.end_date
    progress = ProgressMintScan(localconfig)
    exporter = Exporter(wallet_address, localconfig, TICKER_NTRN)
    txdata = _txdata()

    # Fetch count of transactions to estimate progress more accurately
    count_pages = txdata.get_txs_pages_count(wallet_address, start_date, end_date)
    progress.set_estimate(count_pages)

    # Fetch transactions
    elems = txdata.get_txs_all(wallet_address, progress, start_date, end_date)

    progress.report_message(f"Processing {len(elems)} transactions... ")
    staketaxcsv.ntrn.processor.process_txs(wallet_address, elems, exporter)

    return exporter


def balhistory(wallet_address):
    """ Writes historical balances CSV rows to BalExporter object """
    start_date, end_date = localconfig.start_date, localconfig.end_date
    max_txs = localconfig.limit

    exporter = historical_balances.via_mintscan(
        NTRN_NODE, TICKER_NTRN, wallet_address, max_txs, start_date, end_date)
    return exporter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
