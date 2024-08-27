config = {
    'binance': True,
    'kucoin': False,
    'okx': True,
    'huobi': False,
    'bybit': True,
    'bitfinex': False,
    'gateio': False,


    # Wallet
    'wallets': {
        'binance': 0,
        'kucoin': 0,
        'okx': 0,
        'huobi': 0,
        'bybit': 0,
        'bitfinex': 0,
        'gateio': 0
    },

    'api_keys': {
        'binance': {'api_key': 'lWTBXXMNTUcKXaqekyoq4kswEtfur0gdUVOPE4WYeiFuK1dBfIT21TG7KMNxVsXL', 'api_secret': 'odIZONzwZzCy2656eBkoxPV42jm1TxJfpOmIiiCDd1msHPl8Sdt7PgsC2h37BmJJ'},
        'okx': {
            'api_key': '40c36a5c-caf2-4315-9e4d-7a42afaabf88',
            'api_secret': 'ED0835F499073BE23BED8577C5DCC6E7',
            'password': 'CODDICODDICODi1!'
        },
        'bybit': {
            'api_key': '0Ll6oQnS7peJjfFGzg',
            'secret_key': 'ozefOFJrMUr3tAt4nCGj3knGFujAxcSSmp5H'
        }
    },

    'pairs_cancel': {
        'bybit': ['DASHUSDT']
    },

    'urls': {
        'binance': 'https://api.binance.com/api/v3/ticker/bookTicker',
        'kucoin': 'https://api.kucoin.com/api/v1/market/allTickers',
        'okx': 'https://www.okx.com/api/v5/market/tickers?instType=SPOT',
        'huobi': 'https://api.huobi.pro/market/tickers',
        'bybit': 'https://api.bybit.com/v5/market/tickers?category=spot',
        'bitfinex': 'https://api-pub.bitfinex.com/v2/tickers?symbols=ALL',
        'gateio': 'https://api.gateio.ws/api/v4/spot/tickers'
    },

    'urls_settings': {
        'binance': 'https://api.binance.com/api/v3/exchangeInfo',
        'kucoin': 'https://api.kucoin.com/api/v1/symbols',
        'okx': 'https://www.okx.com/api/v5/public/instruments?instType=SPOT',
        'huobi': 'https://api.huobi.pro/v1/common/symbols',
        'bybit': 'https://api.bybit.com/v2/public/symbols',
        'bitfinex': '',
        'gateio': 'https://api.gateio.ws/api/v4/spot/currency_pairs'
    },
    'urls_withdraw_settings': {
        'okx': 'https://www.okx.com/api/v5/asset/currencies',
    },
}