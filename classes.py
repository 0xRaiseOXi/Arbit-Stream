import requests
import datetime
import asyncio
import hashlib
import httpx
import base64
import time
import hmac

from config import config

class ErrorStatusCode(Exception):
    def __init__(self, message, code=None) -> None:
        super().__init__(message, code)
class ErrorTimeServer(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class HelpClass:
    @staticmethod
    def get_timestamp_okx() -> int:
        now = datetime.datetime.utcnow()
        t = now.isoformat("T", "milliseconds")
        return t + "Z"
    
    @staticmethod
    def get_utc():    
        current_time_milliseconds = time.time() * 1000
        return current_time_milliseconds
    
class OxiNet:
    def __init__(self) -> None:
        """ 
        Инициализация структур данных. 
        """
        # self.data_binance = {'exchange': 'binance'}
        # self.data_kucoin = {'exchange': 'kucoin'}
        # self.data_okx = {'exchange': 'okx'}
        # self.data_bybit = {'exchange': 'bybit'}
        # self.data_huobi = {'exchange': 'hyobi'}
        # self.data_bitfinex = {'exchange': 'bitfinex'}
        # self.data_gateio = {'exchange': 'gateio'}

        self.settings = {'pairs_all': []}
        self.settings_exchanges_names = {}
        self.list_exchanges_data = []

    async def load_settings(self):
        """
        Асинхронная загрузка даннхы с бирж, ключая торговые пары, 
        настройка пар и загрузка сетей для вывода
        """
        start_time_function = time.time()
        async def load_binance_withdraw(self) -> None:
            if config['binance'] == True:
                headers = {
                    'X-MBX-APIKEY': config['api_keys']['binance']['api_key']
                }
                timestamp = int(time.time() * 1000)
                params = {
                    'coin': 'USDT',
                    'timestamp': timestamp
                }
                signature = hmac.new(config['api_keys']['binance']['api_secret'].encode('utf-8'), "&".join([f"{k}={v}" for k, v in params.items()]).encode('utf-8'), hashlib.sha256).hexdigest()
                params['signature'] = signature
                url = f'https://api.binance.com/sapi/v1/capital/config/getall'
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, headers=headers, params=params)
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
                            message = "Не удалось получить информацию о поддерживаемых сетях вывода Binance."
                            raise ErrorStatusCode(message, response.text)
                        self.settings['binance_withdraw'] = settings_binance_withdraw
                except Exception as e:
                    raise ErrorStatusCode(f"Произошла ошибка: {str(e)}")
        
        async def load_okx_withdraw(self) -> None:
            if config['okx'] == True:
                timestamp_okx = HelpClass.get_timestamp_okx()
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
                    res = await client_settings.get(config['urls_withdraw_settings']['okx'], headers=headers)
                    data_settings = res.json()
                    self.settings['okx_withdaw'] = {}
                    for coin in data_settings['data']:
                        ccy = coin['ccy']
                        chain = coin['chain'].split('-')[1]
                        self.settings.setdefault('okx_withdraw', {}).setdefault(ccy, {}).setdefault('networks', {})
                        network_add_data = {
                            'enabledWithdraw': coin['canWd'],
                            'enabledDeposit': coin['canDep'],
                            'fee': coin['minFee'],
                            'min': coin['minWd'],
                            'maxfee': coin['maxFee']
                        }
                        self.settings['okx_withdraw'][ccy]['networks'][chain] = network_add_data

        async def load_bybit_withdraw(self) -> None:
            if config['bybit'] == True:
                recv_window = str(5000)
                timestamp_utc = str(int(HelpClass.get_utc()))
                def genSignature():
                    payload = ''
                    param_str= str(timestamp_utc) + config['api_keys']['bybit']['api_key'] + recv_window + payload
                    hash = hmac.new(bytes(config['api_keys']['bybit']['secret_key'], "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
                    signature = hash.hexdigest()
                    return signature
                headers = {
                    'X-BAPI-SIGN': genSignature(),
                    'X-BAPI-API-KEY': config['api_keys']['bybit']['api_key'],
                    'X-BAPI-TIMESTAMP': timestamp_utc,
                    'X-BAPI-RECV-WINDOW': str(5000)
                }
                async with httpx.AsyncClient() as client_settings_bybit:
                    response = await client_settings_bybit.get('https://api.bybit.com/v5/asset/coin/query-info', headers=headers)
                    data_bybit = response.json()
                    if response.status_code == 200:
                        for coin in data_bybit['result']['rows']:
                            ccy = coin['coin']
                            self.settings.setdefault('bybit_withdraw', {}).setdefault(ccy, {}).setdefault('networks', {})
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
                                self.settings['bybit_withdraw'][ccy]['networks'][chain] = network_add_data
                    else:
                        raise ErrorStatusCode(f'Exchange. Bybit. Ошибка загрузки данных. Статус код {response.status_code} ')
                
        async def load_binance_settings(self) -> None:
            if config['binance'] == True:
                async with httpx.AsyncClient() as client:
                    res = await client.get(config['urls_settings']['binance'])
                    data = res.json()
                    for symbol_binance in data['symbols']:
                        if symbol_binance['status'] == 'TRADING':
                            if symbol_binance['symbol'] not in self.settings:
                                self.settings[symbol_binance['symbol']] = {'symbol': symbol_binance['baseAsset'], 'symbol2': symbol_binance['quoteAsset']}
                                self.settings['pairs_all'].append(symbol_binance['baseAsset'] + '/' + symbol_binance['quoteAsset'])

        async def load_kucoin_settings(self) -> None:
            if config['kucoin'] == True:
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls_settings']['kucoin'])
                    data = response.json()
                    for symbol_kucoin in data['data']:
                        symbol_kucoin_iteration = symbol_kucoin['symbol'].split('-')
                        symbol_kucoin_iteration = symbol_kucoin_iteration[0] + symbol_kucoin_iteration[1]
                        if symbol_kucoin_iteration not in self.settings:
                            self.settings[symbol_kucoin_iteration] = {'symbol': symbol_kucoin['baseCurrency'], 'symbol2': symbol_kucoin['quoteCurrency']}
                            self.settings['pairs_all'].append(symbol_kucoin['baseCurrency'] + '/' + symbol_kucoin['quoteCurrency'])

        async def load_okx_settings(self) -> None:
            if config['okx'] == True:
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls_settings']['okx'])
                    data = response.json()

                    for symbol_okx in data['data']:
                        symbol_okx_iteration = symbol_okx['instId'].split('-')
                        symbol_okx_iteration = symbol_okx_iteration[0] + symbol_okx_iteration[1]
                        if symbol_okx_iteration not in self.settings:
                            self.settings[symbol_okx_iteration] = {'symbol': symbol_okx['baseCcy'], 'symbol2': symbol_okx['quoteCcy']}
                            self.settings['pairs_all'].append(symbol_okx['baseCcy'] + '/' + symbol_okx['quoteCcy'])

        async def load_huobi_settings(self) -> None:
            if config['huobi'] == True:
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls_settings']['huobi'])
                    data = response.json()
                    for symbol_huobi in data['data']:
                        symbol_huobi_iteration = symbol_huobi['base-currency'].upper() + symbol_huobi['quote-currency'].upper()
                        if symbol_huobi_iteration not in self.settings:
                            self.settings[symbol_huobi_iteration] = {'symbol': symbol_huobi['base-currency'].upper(), 'symbol2': symbol_huobi['quote-currency'].upper()}
                            self.settings['pairs_all'].append(symbol_huobi['base-currency'].upper() + '/' + symbol_huobi['quote-currency'].upper())   
        
        async def load_bybit_settings(self) -> None:
            if config['bybit'] == True:
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls_settings']['bybit'])
                    data = response.json()
                    for symbol_bybit in data['result']:
                        symbol_bybit_iteration = symbol_bybit['base_currency'] + symbol_bybit['quote_currency']
                        if symbol_bybit_iteration not in self.settings:
                            self.settings[symbol_bybit_iteration] = {'symbol': symbol_bybit['base_currency'], 'symbol2': symbol_bybit['quote_currency']}
                            self.settings['pairs_all'].append(symbol_bybit['base_currency'] + '/' + symbol_bybit['quote_currency'])  


        async def load_gateio_settings(self) -> None:
            if config['gateio'] == True:
                headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls_settings']['gateio'], headers=headers)
                    data = response.json()
                    for symbol_gateio in data:
                        symbol_gateio_i = symbol_gateio['id'].split('_')
                        symbol_gateio_i = symbol_gateio_i[0] + symbol_gateio_i[1]
                        if symbol_gateio_i not in self.settings:
                            self.settings[symbol_gateio_i] = {'symbol': symbol_gateio['base'], 'symbol2': symbol_gateio['quote']} 
                            self.settings['pairs_all'].append(symbol_gateio['base'] + '/' + symbol_gateio['quote'])  

        list_function = [load_binance_withdraw, load_okx_withdraw, load_bybit_withdraw, load_binance_settings, load_kucoin_settings, load_okx_settings, load_huobi_settings, load_bybit_settings, load_gateio_settings]
        tasks = []
        for function in list_function:
            task = asyncio.create_task(function(self))
            tasks.append(task)

        await asyncio.gather(*tasks)
        print('Настройки загружены. Время загрузки: ', time.time() - start_time_function)

    async def load_symbols_exchanges(self) -> None:
        start_program_data_time = time.time()
        async def load_binance(self) -> None:
            if config['binance'] == True:
                data_binance = {'exchange': 'binance'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls']['binance'])
                    data = response.json()
                    for i in data:
                        if float(i['askPrice']) > 0.0:
                            if i['symbol'] in self.settings:
                                symbol_settings = self.settings[i['symbol']]['symbol']
                                for j in self.settings['binance_withdraw'][symbol_settings]['networks'].values():
                                    if j['enabledWithdraw'] == False or j['enabledDeposit'] == False:
                                        continue
                                data_binance[i['symbol']] = {'ask': i['askPrice'], 'bid': i['bidPrice']}
                self.list_exchanges_data.append(data_binance)
        async def load_kucoin(self) -> None:
            if config['kucoin'] == True:
                data_kucoin = {'exchange': 'kucoin'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls']['kucoin'])
                    data = response.json()
                    for i in data['data']['ticker']:
                        symbol = i['symbol'].split('-')
                        symbol = symbol[0] + symbol[1]
                        data_kucoin[symbol] = {'ask': i['sell'], 'bid': i['buy']}
                self.list_exchanges_data.append(data_kucoin)
        
        async def load_okx(self) -> None:
            if config['okx'] == True:
                data_okx = {'exchange': 'okx'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls']['okx'])
                    data = response.json()
                    for i in data['data']:
                        symbol = i['instId'].split('-')
                        symbol = symbol[0] + symbol[1]
                        data_okx[symbol] = {'ask': i['askPx'], 'bid': i['bidPx']}
                self.list_exchanges_data.append(data_okx)

        async def load_huobi(self):
            if config['huobi'] == True:
                data_huobi = {'exchange': 'huobi'}
                pass
        
        async def load_bybit(self): 
            if config['bybit'] == True:
                data_bybit = {'exchange': 'bybit'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls']['bybit'])
                    data = response.json()
                    for i in data['result']['list']:
                        data_bybit[i['symbol']] = {'ask': i['ask1Price'], 'bid': i['bid1Price']}
                self.list_exchanges_data.append(data_bybit)
        async def load_bitfinex(self):
            if config['bitfinex'] == True:
                data_bitfinex = {'exchange': 'bitfinex'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls']['bitfinex'])
                    data = response.json()
                    for i in data:
                        pass
        async def load_gateio(self):
            if config['gateio'] == True:
                headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
                data_gateio = {'exchange': 'gateio'}
                async with httpx.AsyncClient() as client:
                    response = await client.get(config['urls']['gateio'], headers=headers)
                    data = response.json()
                    for i in data:
                        if i['lowest_ask'] != '' and i['highest_bid'] != '':
                            symbol = i['currency_pair'].split('_')
                            symbol = symbol[0] + symbol[1]
                            data_gateio[symbol] = {'ask': i['lowest_ask'], 'bid': i['highest_bid']}
                self.list_exchanges_data.append(data_gateio)
        
        list_functions = [load_binance, load_kucoin, load_okx, load_huobi, load_bybit, load_bitfinex, load_gateio]
        tasks = []
        for function in list_functions:
            task = asyncio.create_task(function(self))
            tasks.append(task)
        await asyncio.gather(*tasks)
        print('Данные загружены. Время загрузки: ', time.time() -start_program_data_time)
        
    def symbols_exchange(self) -> None:
        data_all_symbols = []
        symbols_all = {}
        for coin in self.settings['pairs_all']:
            coin_key = coin.split('/')[0]
            coins =[]
            for symbol_coin in self.settings['pairs_all']:
                if coin_key == symbol_coin.split('/')[0]:
                    coins.append(symbol_coin)
            symbols_all[coin_key] = coins
        for key, symbols in symbols_all.items():
            symbols_list_exchange = {}
            for exchange in self.list_exchanges_data:
                symbols_list = {}
                for symbol in symbols:
                    if exchange['exchange'] == 'binance' and symbol.split('/')[1] == 'VAI':
                        continue
                    symbol_key_data = symbol.split('/')
                    symbol_key_data = symbol_key_data[0] + symbol_key_data[1]
                    try:
                        symbol_ask = exchange[symbol_key_data]['ask']
                        symbol_bid = exchange[symbol_key_data]['bid']
                    except KeyError:
                        continue
                    if symbol.split('/')[1] != 'USDT':
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
                            data_all_symbols.append([end, min_key_ask, max_key_bid, min_ex_ask, symbol_ex, max_ex_bid, symbol_ex_bid])
        max_element = sorted(data_all_symbols, key=lambda x: x[0], reverse=True)
        
        index = 0
        while True:
            try:
                element_key_symbol = max_element[index]
                print(index, element_key_symbol)
                index += 1
            except IndexError:
                break

    async def run_function(self) -> None:
        task_settings = asyncio.create_task(self.load_settings())   
        await asyncio.wait_for(task_settings, None)
        while True:
            flag = int(input('Подтвердите обновление цикла: '))
            if flag == 1:
                data = asyncio.create_task(self.load_symbols_exchanges())   
                await asyncio.wait_for(data, None)
                self.symbols_exchange()
       
            elif flag == 0:
                raise SystemExit
            else:
                continue
        

    def run(self):
        asyncio.run(self.run_function())    

program = OxiNet()
program.run()