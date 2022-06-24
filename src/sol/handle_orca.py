from common.make_tx import make_swap_tx
from sol.handle_simple import handle_unknown_detect_transfers
from sol.constants import CURRENCY_SOL
from sol.util_sol import FEE_THRESHOLD


def handle_orca_swap_v2(exporter, txinfo):
    transfers_in, transfers_out, _ = txinfo.transfers_net

    if len(transfers_in) == 1 and len(transfers_out) == 1:
        sent_amount, sent_currency, _, _ = transfers_out[0]
        received_amount, received_currency, _, _ = transfers_in[0]
        row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
        exporter.ingest_row(row)
    elif len(transfers_in) == 2 and len(transfers_out) == 1:
        # Detect case where if there's extra SOL transfer in with small amount
        amt1, cur1, _, _ = transfers_in[0]
        amt2, cur2, _, _ = transfers_in[1]

        if cur1 == CURRENCY_SOL and amt1 < FEE_THRESHOLD:
            sent_amount, sent_currency, _, _ = transfers_out[0]
            received_amount, received_currency = amt2, cur2
            row = make_swap_tx(txinfo, sent_amount, sent_currency, received_amount, received_currency)
            exporter.ingest_row(row)
    else:
        handle_unknown_detect_transfers(exporter, txinfo)
