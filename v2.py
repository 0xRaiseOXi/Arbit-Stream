import requests
import time
import asyncio
import httpx
from config import config
import sys
import os
import hmac
import hashlib
import datetime
import base64



class ErrorStatusCode(Exception):
    def __init__(self, message):
        super().__init__(message)

class ErrorTimeServer(Exception):
    def __init__(self, message):
        super().__init__(message)
# data = {}
data_binance = {'exchange': 'binance'}
data_kucoin = {'exchange': 'kucoin'}
data_okx = {'exchange': 'okx'}
data_huobi = {'exchange': 'huobi'}
data_bybit = {'exchange': 'bybit'}
data_bitfines = {'exchange': 'bitfinex'}
data_gateio = {'exchange': 'gateio'}


binance_networks = {'exchange': 'binance'}

list_data = [data_binance, data_kucoin, data_okx, data_huobi, data_bybit, data_bitfines, data_gateio]

urls = [
    {'exchange': 'binance', 'url': 'https://api.binance.com/api/v3/ticker/bookTicker', 'url_settings': 'https://api.binance.com/api/v3/exchangeInfo'},
    {'exchange': 'kucoin', 'url': 'https://api.kucoin.com/api/v1/market/allTickers', 'url_settings': 'https://api.kucoin.com/api/v1/symbols'},
    {'exchange': 'okx', 'url': 'https://www.okx.com/api/v5/market/tickers?instType=SPOT', 'url_settings': 'https://www.okx.com/api/v5/public/instruments?instType=SPOT'},
    {'exchange': 'huobi', 'url': 'https://api.huobi.pro/market/tickers', 'url_settings': 'https://api.huobi.pro/v1/common/symbols'},
    {'exchange': 'bybit', 'url': 'https://api.bybit.com/v5/market/tickers?category=spot', 'url_settings': 'https://api.bybit.com/v2/public/symbols'},
    {'exchange': 'bitfinex', 'url': 'https://api-pub.bitfinex.com/v2/tickers?symbols=ALL'},
    {'exchange': 'gateio', 'url': 'https://api.gateio.ws/api/v4/spot/tickers', 'url_settings': 'https://api.gateio.ws/api/v4/spot/currency_pairs'}
]
new_list_data = []
settings_keys = {}


settings_exchanges_names = {''}

keys_pairs_exchanges = {}
settings = {'pairs_all': []}
async def load_settings_pair():

    for i in urls:
        if i['exchange'] == 'binance' and config[i['exchange']] == True:
            async with httpx.AsyncClient() as client:
                res = await client.get(i['url_settings'])
                data = res.json()
            print(i['exchange'])
            for symbol_binance in data['symbols']:
                if symbol_binance['status'] == 'TRADING':
                    if symbol_binance['symbol'] not in settings:
                        settings[symbol_binance['symbol']] = {'symbol': symbol_binance['baseAsset'], 'symbol2': symbol_binance['quoteAsset']}
                        settings['pairs_all'].append(symbol_binance['baseAsset'] + '/' + symbol_binance['quoteAsset'])
             
        
            headers = {
                'X-MBX-APIKEY': config['api_keys']['binance']['api_key'],
            }
            timestamp = int(time.time() * 1000)
            params = {
                'coin': "USDT",
                'timestamp': timestamp,
            }
            signature = hmac.new(config['api_keys']['binance']['api_secret'].encode('utf-8'), "&".join([f"{k}={v}" for k, v in params.items()]).encode('utf-8'), hashlib.sha256).hexdigest()
            params['signature'] = signature
            url = f'https://api.binance.com/sapi/v1/capital/config/getall'
            try:
                response = requests.get(url, headers=headers, params=params)
        
                if response.status_code == 200:
                    data = response.json()      
                    settings_binance_withdraw = {}
                 
                 
                    if data:
                        for coin in data:
                            networks_add = settings_binance_withdraw[coin['coin']] = {
                                'networks': {}
                            }
                            
                            for network in coin['networkList']:
                                try:
                                    network_add_data = {
                                        'enabledWithdraw': network['withdrawEnable'],
                                        'enabledDeposit': network['depositEnable'],
                                        'fee': network['withdrawFee'],
                                        'min': network['withdrawMin']
                                    }
                                    networks_add['networks'][network['network']] = network_add_data
                                except KeyError as e:
                                    raise ErrorTimeServer(e)
                else:
                    print(f"Не удалось получить информацию о поддерживаемых сетях вывода Binance.")
                settings['binance_withdraw'] = settings_binance_withdraw
            except Exception as e:
                return f"Произошла ошибка: {str(e)}"
        
           

        if i['exchange'] == 'kucoin' and config[i['exchange']] == True:
            async with httpx.AsyncClient() as client:
                res = await client.get(i['url_settings'])
                data = res.json()
            print(i['exchange'])
            print(len(data['data']))
            for symbol_kucoin in data['data']:
                symbol_kucoin_iteration = symbol_kucoin['symbol'].split('-')
                symbol_kucoin_iteration = symbol_kucoin_iteration[0] + symbol_kucoin_iteration[1]
                if symbol_kucoin_iteration not in settings:
                    settings[symbol_kucoin_iteration] = {'symbol': symbol_kucoin['baseCurrency'], 'symbol2': symbol_kucoin['quoteCurrency']}
                    settings['pairs_all'].append(symbol_kucoin['baseCurrency'] + '/' + symbol_kucoin['quoteCurrency'])
                    # settings['pairs_all'].append(symbol_kucoin['baseCurrency'])
                    # settings['quote_all'].append(symbol_kucoin['quoteCurrency'])

        if i['exchange'] == 'okx' and config[i['exchange']] == True:
            URL = 'https://www.okx.com/api/v5/asset/currencies'
            def get_time():
                now = datetime.datetime.utcnow()
                t = now.isoformat("T", "milliseconds")
                return t + "Z"
            timestamp_okx = get_time()
            def signature(method, request_path, body):
                if str(body) == '{}' or str(body) == 'None':
                    body = ''
                message = str(timestamp_okx) + str.upper(method) + request_path + str(body)
                mac = hmac.new(bytes(config['api_keys']['okx']['api_secret'], encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
                d = mac.digest()
                return base64.b64encode(d)

        
            sign = signature('GET', '/api/v5/asset/currencies', {})
            
            headers = {
                'OK-ACCESS-KEY': config['api_keys']['okx']['api_key'],
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp_okx,
                'OK-ACCESS-PASSPHRASE': config['api_keys']['okx']['password'],
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client_settings:
                res = await client_settings.get(URL, headers=headers)
                data_settings = res.json()
                settings['okx_withdaw'] = {}
                for coin in data_settings['data']:
                    ccy = coin['ccy']
                    chain = coin['chain'].split('-')[1]
                    settings.setdefault('okx_withdraw', {}).setdefault(ccy, {}).setdefault('networks', {})
                    network_add_data = {
                        'enabledWithdraw': coin['canWd'],
                        'enabledDeposit': coin['canDep'],
                        'fee': coin['minFee'],
                        'min': coin['minWd'],
                        'maxfee': coin['maxFee']
                    }
                    settings['okx_withdraw'][ccy]['networks'][chain] = network_add_data
            async with httpx.AsyncClient() as client:
                res = await client.get(i['url_settings'])
                data = res.json()
            print(i['exchange'])
            print(len(data['data']))
            for symbol_okx in data['data']:
                symbol_okx_iteration = symbol_okx['instId'].split('-')
                symbol_okx_iteration = symbol_okx_iteration[0] + symbol_okx_iteration[1]
                if symbol_okx_iteration not in settings:
                    settings[symbol_okx_iteration] = {'symbol': symbol_okx['baseCcy'], 'symbol2': symbol_okx['quoteCcy']}
                    settings['pairs_all'].append(symbol_okx['baseCcy'] + '/' + symbol_okx['quoteCcy'])
                    # settings['pairs_all'].append(symbol_okx['baseCcy'])
                    # settings['quote_all'].append(symbol_okx['quoteCcy'])

        if i['exchange'] == 'huobi' and config[i['exchange']] == True:
            async with httpx.AsyncClient() as client:
                res = await client.get(i['url_settings'])
                data = res.json()
            print(i['exchange'])
            for symbol_huobi in data['data']:
                symbol_huobi_iteration = symbol_huobi['symbol'].upper()
                if symbol_huobi_iteration not in settings:
                    settings[symbol_huobi_iteration] = {'symbol': symbol_huobi['base-currency'].upper(), 'symbol2': symbol_huobi['quote-currency'].upper()}
                    settings['pairs_all'].append(symbol_huobi['base-currency'].upper() + '/' + symbol_huobi['quote-currency'].upper())   
                    # settings['pairs_all'].append(symbol_huobi['base-currency'].upper())
                    # settings['quote_all'].append(symbol_huobi['quote-currency'].upper())

        if i['exchange'] == 'bybit' and config[i['exchange']] == True:
            recv_window = str(5000)
            def get_utc():    
                current_time_milliseconds = time.time() * 1000
                return current_time_milliseconds
            timestamp_utc = str(int(get_utc()))
            def genSignature():
                payload = ''
                param_str= str(timestamp_utc) + config['api_keys']['bybit']['api_key'] + recv_window + payload
                hash = hmac.new(bytes(config['api_keys']['bybit']['secret_key'], "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
                signature = hash.hexdigest()
                return signature
            auth_token = genSignature()
            headers = {
                'X-BAPI-SIGN': auth_token,
                'X-BAPI-API-KEY': config['api_keys']['bybit']['api_key'],
                'X-BAPI-TIMESTAMP': timestamp_utc,
                'X-BAPI-RECV-WINDOW': str(5000)
            }
            async with httpx.AsyncClient() as client_settings_bybit:
                res = await client_settings_bybit.get('https://api.bybit.com/v5/asset/coin/query-info', headers=headers)
                data_bybit = res.json()
                if res.status_code == 200:
                    for coin in data_bybit['result']['rows']:
                        ccy = coin['coin']
                        settings.setdefault('bybit_withdraw', {}).setdefault(ccy, {}).setdefault('networks', {})
                        for coin_chains in coin['chains']:
                            chain = coin_chains['chain']
                            flag_withdraw = False
                            flag_deposit = False
                            if coin_chains['chainDeposit'] == '1':
                                flag_deposit = True
                            if coin_chains['chainWithdraw'] == '1':
                                flag_withdraw = True
                   
                            network_add_data = {
                                'enabledWithdraw': flag_withdraw,
                                'enabledDeposit': flag_deposit,
                                'fee': coin_chains['withdrawFee'],
                                'min': coin_chains['withdrawMin']
                            }
                            settings['bybit_withdraw'][ccy]['networks'][chain] = network_add_data
                else:
                    raise ErrorStatusCode(f'Exchange. Bybit. Ошибка загрузки данных. Статус код {res.status_code} ')
                
            async with httpx.AsyncClient() as client:
                res = await client.get(i['url_settings'])
                data = res.json()
            print(i['exchange'])
            print(len(data['result']))

            for symbol_bybit in data['result']:
                if symbol_bybit['name'] not in settings:
                    settings[symbol_bybit['name']] = {'symbol': symbol_bybit['base_currency'], 'symbol2': symbol_bybit['quote_currency']}
                    settings['pairs_all'].append(symbol_bybit['base_currency'] + '/' + symbol_bybit['quote_currency'])  
                    # settings['pairs_all'].append(symbol_bybit['base_currency'])
                    # settings['quote_all'].append(symbol_bybit['quote_currency'])
               
        if i['exchange'] == 'gateio' and config[i['exchange']] == True:
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
            async with httpx.AsyncClient() as client:
                res = await client.get(i['url_settings'], headers=headers)
                data = res.json()
            # print(len(data))
            print(i['exchange'])
            for symbol_gateio in data:
                symbol_gateio_i = symbol_gateio['id'].split('_')
                symbol_gateio_i = symbol_gateio_i[0] + symbol_gateio_i[1]
                if symbol_gateio_i not in settings:
                    settings[symbol_gateio_i] = {'symbol': symbol_gateio['base'], 'symbol2': symbol_gateio['quote']} 
                    settings['pairs_all'].append(symbol_gateio['base'] + '/' + symbol_gateio['quote'])  
                    # settings['pairs_all'].append(symbol_gateio['base'])  
                    # settings['quote_all'].append(symbol_gateio['quote'])

async def load_binance():
    if config[urls[0]['exchange']] == True:
        new_data_binance = {'exchange': 'binance'}
        async with httpx.AsyncClient() as client:
            res = await client.get(urls[0]['url'])
            res = res.json()
        for i in res:
            if float(i['askPrice']) > 0.0:
                if i['symbol'] in settings:
                    symbol_settings = settings[i['symbol']]['symbol']
                    if len(settings['binance_withdraw'][symbol_settings]['networks']) == 1:
                        for j in settings['binance_withdraw'][symbol_settings]['networks'].values():
                            if j['enabledWithdraw'] == False or j['enabledDeposit'] == False:
                                continue
                    data_binance[i['symbol']] = {'ask': i['askPrice'], 'bid': i['bidPrice']}
                    new_data_binance[i['symbol']] = {'ask': i['askPrice'], 'bid': i['bidPrice']}
        new_list_data.append(new_data_binance)

async def load_kucoin():
    if config[urls[1]['exchange']] == True:
        async with httpx.AsyncClient() as client:
            res = await client.get(urls[1]['url'])
            res = res.json()
        for i in res['data']['ticker']:
            symbol = i['symbol'].split('-')
            symbol = symbol[0] + symbol[1]
            data_kucoin[symbol] = {'ask': i['sell'], 'bid': i['buy']}
async def load_okx():
    if config[urls[2]['exchange']] == True:
        new_data_okx = {'exchange': 'okx'}
        async with httpx.AsyncClient() as client:
            res = await client.get(urls[2]['url'])
            res = res.json()
        for i in res['data']:
            symbol = i['instId'].split('-')
            symbol = symbol[0] + symbol[1]
            data_okx[symbol] = {'ask': i['askPx'], 'bid': i['bidPx']}
            new_data_okx[symbol] = {'ask': i['askPx'], 'bid': i['bidPx']}
        new_list_data.append(new_data_okx)
async def load_huobi():
    if config[urls[3]['exchange']] == True:
        pass
async def load_bybit(): 
    if config[urls[4]['exchange']] == True:
        new_data_bybit = {'exchange': 'bybit'}
        async with httpx.AsyncClient() as client:
            res = await client.get(urls[4]['url'])
            res = res.json()
        for i in res['result']['list']:
            data_bybit[i['symbol']] = {'ask': i['ask1Price'], 'bid': i['bid1Price']}
            new_data_bybit[i['symbol']] = {'ask': i['ask1Price'], 'bid': i['bid1Price']}
        new_list_data.append(new_data_bybit)

async def load_bitfinex():
    if config[urls[5]['exchange']] == True:
        async with httpx.AsyncClient() as client:
            res = await client.get(urls[5]['url'])
            res = res.json()
        for i in res:
            if i[0][0] == 't':
                pass
    ## ????
async def load_gateio():
    if config[urls[6]['exchange']] == True:
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

        async with httpx.AsyncClient() as client:
            res = await client.get(urls[6]['url'], headers=headers)
            res = res.json()
        for i in res:
            if i['lowest_ask'] != '' and i['highest_bid'] != '':
                symbol = i['currency_pair'].split('_')
                symbol = symbol[0] + symbol[1]
                data_gateio[symbol] = {'ask': i['lowest_ask'], 'bid': i['highest_bid']}
    
async def loading_data_index():
    start_load_data = time.time()
    task_load = asyncio.create_task(load_settings_pair())
    await asyncio.wait([task_load])
    print('Данные заружены. Время загрузки: ', time.time() - start_load_data)
    while True:
        flag = int(input('Подтвердите обновление цикла: '))
        if flag == 1:
            print('Загружаю данные...')
            list_index = [load_binance, load_kucoin, load_okx, load_huobi, load_bybit, load_bitfinex, load_gateio]
            tasks = []
            for function in list_index:
                task = asyncio.create_task(function())
                tasks.append(task)

            await asyncio.gather(*tasks)
            symbols()
        elif flag == 0:
            raise SystemExit
        else:
            continue


def symbols():  
    data_all_symbols = []
    symbols_all = {}
    for coin in settings['pairs_all']:
        coin_key = coin.split('/')[0]
        coins = []
        for symbol_coin in settings['pairs_all']:
            if coin_key == symbol_coin.split('/')[0]:
                coins.append(symbol_coin)
        symbols_all[coin_key] = coins

    for key, symbols in symbols_all.items():
        symbols_list_exchange = {}
        for exchange in new_list_data:
            symbols_list = {}
            for symbol in symbols: 
                symbol_key_data = symbol.split('/')
                symbol_key_data = symbol_key_data[0] + symbol_key_data[1]
                try:
                    symbol_ask = exchange[symbol_key_data]['ask']
                    symbol_bid = exchange[symbol_key_data]['bid']
                except KeyError:
                    continue
                if symbol.split('/')[1] != 'USDT':
                    if exchange['exchange'] == 'binance' and symbol.split('/')[1] == 'VAI':
                        continue
                    try:
                        symbol_quote_asset = symbol.split('/')[1] + 'USDT'
                        symbol_quote_price_ask = exchange[symbol_quote_asset]['ask']
                        symbol_quote_price_bid = exchange[symbol_quote_asset]['bid']
                        symbol_ask = float(symbol_ask) * float(symbol_quote_price_ask)
                        symbol_bid = float(symbol_bid) * float(symbol_quote_price_bid)
                    except (KeyError, ValueError):
                        symbol_quote_asset = 'USDT' + symbol.split('/')[1]
                        symbol_quote_price_ask = exchange[symbol_quote_asset]['ask']
                        symbol_quote_price_bid = exchange[symbol_quote_asset]['bid']
                        symbol_ask = float(symbol_ask) / float(symbol_quote_price_ask)
                        symbol_bid = float(symbol_bid) / float(symbol_quote_price_bid)

                symbols_list[symbol] = {'ask': symbol_ask, 'bid': symbol_bid} 
            if symbols_list: 
                symbols_list_exchange[exchange['exchange']] = symbols_list

        if symbols_list_exchange:
            min_key_ask = 0
            max_key_bid = 0
            min_ex_ask = ''
            max_ex_bid = ''
            symbol_ex = ''
            symbol_ex_bid = ''
            for exchange_key, symbols_key in symbols_list_exchange.items(): 
                min_key = min(symbols_key, key=lambda k: float(symbols_key[k]['ask']))
                if min_key:
                    if min_key_ask == 0:
                        min_key_ask = symbols_key[min_key]['ask']
                        min_ex_ask = exchange_key
                        symbol_ex = min_key
                    else:
                        if float(symbols_key[min_key]['ask']) < float(min_key_ask):
                            min_key_ask = symbols_key[min_key]['ask']
                            min_ex_ask = exchange_key
                max_key = max(symbols_key, key=lambda k: float(symbols_key[k]['bid']))
                if max_key:
                    if float(symbols_key[max_key]['bid']) > float(max_key_bid):
                        max_key_bid = symbols_key[max_key]['bid']
                        max_ex_bid = exchange_key
                        symbol_ex_bid = max_key
            if min_key_ask != 0 and max_key_bid != 0:
                if min_ex_ask != max_ex_bid:
                    end = 100 - float(min_key_ask) / float(max_key_bid) * 100
                    if end > 0 and end < 10:
                        # print(float("{:.2f}".format(end)), min_key_ask, max_key_bid, min_ex_ask, f'{symbol_ex}', '-->', max_ex_bid, f'{symbol_ex_bid}')
                        data_all_symbols.append([end, min_key_ask, max_key_bid, min_ex_ask, symbol_ex, max_ex_bid, symbol_ex_bid])
 
    max_element = sorted(data_all_symbols, key=lambda x: x[0], reverse=True)
    i = 1
    i_iterable = 11
    i_i = 1

    while i != i_iterable:
        print(i_i,'.', '----------------------')
        print(max_element[i])
        print(max_element[i][3], max_element[i][-2])
        element_key_symbol = max_element[i][4].split('/')[0]
        print(max_element[i][3] + '_withdraw')
        if len(settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks']) > 1 and len(settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks']) == 1:
            network_exchange_2 = settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks']
            for network, data_network in settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks'].items():
                if network == next(iter(network_exchange_2)):
                    print('!!!!!!!!!!!1')
                    print(network_exchange_2)
                    print(network, data_network)
                    price_symbol_fee = float(network_exchange_2[next(iter(network_exchange_2))]['fee']) * float(max_element[i][1])
                    print('Комиссия: ', price_symbol_fee,'USDT')
                    end_fee_balance = 100 - (50 / (50 + float(price_symbol_fee)) * 100)
                    print(end_fee_balance)
                    if end_fee_balance < max_element[i][0]:
                        print('___________________SUCCESS________________\nМонета готова к арбитражу!')



        elif len(settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks']) == 1 and len(settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks']) > 1:
            network_exchange_1 = settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks']
            for network, data_network in settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks'].items():
                if network == next(iter(network_exchange_1)):
                    print('!!!!!!!!!!!2')
                    print(network_exchange_1)
                    print(network, data_network)
                    price_symbol_fee = float(network_exchange_1[next(iter(network_exchange_1))]['fee']) * float(max_element[i][1])
                    print('Комиссия: ', price_symbol_fee,'USDT')
                    end_fee_balance = 100 - (50 / (50 + float(price_symbol_fee)) * 100)
                    print(end_fee_balance)
                    if end_fee_balance < max_element[i][0]:
                        print('___________________SUCCESS________________\nМонета готова к арбитражу!')
        elif len(settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks']) > 1 and len(settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks']) > 1:
            print(settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks'])
            print(settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks'])
         
        
        else:
            print('ELSE')
            data_exchange = settings[max_element[i][3] + '_withdraw'][element_key_symbol]['networks']
            data_exchange_2 = settings[max_element[i][-2] + '_withdraw'][element_key_symbol]['networks']
            print(data_exchange, data_exchange_2)
            price_symbol_fee = float(data_exchange[next(iter(data_exchange))]['fee']) * float(max_element[i][1])
            print('Комиссия: ', price_symbol_fee,'USDT')
            if data_exchange[next(iter(data_exchange))]['enabledWithdraw'] == False or data_exchange_2[next(iter(data_exchange_2))]['enabledDeposit'] == False:
                i_iterable += 1
                i += 1
                print(data_exchange, data_exchange_2)
                print('____PASS____')
                continue
            end_fee_balance = 100 - (50 / (50 + float(price_symbol_fee)) * 100)
            print(end_fee_balance)
            if end_fee_balance < max_element[i][0]:
                print('___________________SUCCESS________________\nМонета готова к арбитражу!')
        
        print('----------------------')
        i_i += 1
        i += 1


def main():
    asyncio.run(loading_data_index())

main()