from staketaxcsv.common.Exporter import Row
from staketaxcsv.common.ExporterTypes import TX_TYPE_AIRDROP
from staketaxcsv.luna2.constants import CURRENCY_LUNA2, EXCHANGE_LUNA2


def make_genesis_airdrop1_tx(amount_luna, wallet_address):
    row = Row(
        timestamp="2022-05-28 06:00:00",  # timestamp of height 1 (https://phoenix-lcd.terra.dev/blocks/1)
        tx_type=TX_TYPE_AIRDROP,
        received_amount=amount_luna,
        received_currency=CURRENCY_LUNA2,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=EXCHANGE_LUNA2,
        wallet_address=wallet_address,
        txid="luna2_genesis_airdrop1",
        url="",
        block_svc_hash=""
    )
    return row


def make_vesting_airdrop_tx(amount_luna, wallet_address, timestamp):
    txid = "luna2_vesting_airdrop_" + timestamp.split(" ")[0].replace("-", "")  # "2023-05-28 00:00:00" -> "20230528"
    row = Row(
        timestamp=timestamp,
        tx_type=TX_TYPE_AIRDROP,
        received_amount=amount_luna,
        received_currency=CURRENCY_LUNA2,
        sent_amount="",
        sent_currency="",
        fee="",
        fee_currency="",
        exchange=EXCHANGE_LUNA2,
        wallet_address=wallet_address,
        txid=txid,
        url=""
    )
    return row
