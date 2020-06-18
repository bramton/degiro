import requests
import json
import getpass
from datetime import datetime
from collections import defaultdict

class degiro:
    def __init__(self):
        self.user = dict()
        self.data = None
    
    def login(self, conf_path=None, with2fa:bool=False):
        if(conf_path==None):
            conf = dict(username=input("Username: "), password=getpass.getpass())
        else:
            conf = json.load(open(conf_path))
        self.sess = requests.Session()
        
        # Login
        url = 'https://trader.degiro.nl/login/secure/login'
        payload = {'username': conf['username'],
                   'password': conf['password'],
                   'isPassCodeReset': False,
                   'isRedirectToMobile': False}
        header={'content-type': 'application/json'}

        if(with2fa):
            payload['oneTimePassword']=getpass.getpass("2FA Token: ")
            url+='/totp'
        r = self.sess.post(url, headers=header, data=json.dumps(payload))
        print('Login')
        print('\tStatus code: {}'.format(r.status_code))

        # Get session id
        self.sessid = r.headers['Set-Cookie']
        self.sessid = self.sessid.split(';')[0]
        self.sessid = self.sessid.split('=')[1]

        print('\tSession id: {}'.format(self.sessid))
        
    # This contain loads of user data, main interest here is the 'intAccount'
    def getConfig(self):
        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get config')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()
        self.user['intAccount'] = data['data']['intAccount']
        
        print('\tAccount id: {}'.format(self.user['intAccount']))
        
    # This gets a lot of data, orders, news, portfolio, cash funds etc.
    def getData(self):
        url = 'https://trader.degiro.nl/trading/secure/v5/update/'
        url += str(self.user['intAccount'])+';'
        url += 'jsessionid='+self.sessid
        payload = {'portfolio': 0,
                   'totalPortfolio': 0,
                   'orders': 0,
                   'historicalOrders': 0,
                   'transactions': 0,
                   'alerts': 0,
                   'cashFunds': 0,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get data')
        print('\tStatus code: {}'.format(r.status_code))

        self.data = r.json()

    # Get the cash funds
    def getCashFunds(self):
        if self.data == None:
            self.getData()       
        cashFunds = dict()
        for cf in self.data['cashFunds']['value']:
            entry = dict()
            for y in cf['value']:
                # Useful if the currency code is the key to the dict
                if y['name'] == 'currencyCode':
                    key = y['value']
                    continue
                entry[y['name']] = y['value']
            cashFunds[key] = entry
        return cashFunds
    
    # Only returns a summary of the portfolio
    def getPortfolioSummary(self):
        pf = self.getPortfolio()
        cf = self.getCashFunds()
        tot = 0
        for eq in pf['PRODUCT'].values():
            tot += eq['value']     

        pfSummary = dict()
        pfSummary['equity'] = tot
        pfSummary['cash'] = cf['EUR']['value']
        return pfSummary
    
    # Returns the entire portfolio
    def getPortfolio(self):
        if self.data == None:
            self.getData()       
        portfolio = []
        for row in self.data['portfolio']['value']:
            entry = dict()
            for y in row['value']:
                k = y['name']
                v = None
                if 'value' in y:
                    v = y['value']
                entry[k] = v
            # Also historic equities are returned, let's omit them
            if entry['size'] != 0:
                portfolio.append(entry)

        ## Restructure portfolio and add extra data
        portf_n = defaultdict(dict)
        # Restructuring
        for r in portfolio:
            pos_type = r['positionType']
            pid = r['id'] # Product ID
            del(r['positionType'])
            del(r['id'])
            portf_n[pos_type][pid]= r

        # Adding extra data
        url = 'https://trader.degiro.nl/product_search/secure/v5/products/info'
        params = {'intAccount': str(self.user['intAccount']),
                  'sessionId': self.sessid}
        header={'content-type': 'application/json'}
        pid_list = list(portf_n['PRODUCT'].keys())
        r = self.sess.post(url, headers=header, params=params, data=json.dumps(pid_list))
        print('\tGetting extra data')
        print('\t\tStatus code: {}'.format(r.status_code))

        for k,v in r.json()['data'].items():
            del(v['id'])
            # Some bonds tend to have a non-unit size
            portf_n['PRODUCT'][k]['size'] *= v['contractSize']
            portf_n['PRODUCT'][k].update(v)

        return portf_n

    # Returns all account transactions
    #  fromDate and toDate are strings in the format: dd/mm/yyyy
    def getAccountOverview(self, fromDate, toDate):
        url = 'https://trader.degiro.nl/reporting/secure/v4/accountoverview'
        payload = {'fromDate': fromDate,
                   'toDate': toDate,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get account overview')
        print('\tStatus code: {}'.format(r.status_code))
        
        data = r.json()
        movs = []
        for rmov in data['data']['cashMovements']:
            mov = dict()
            # Reformat timezone part: +01:00 -> +0100
            date = ''.join(rmov['date'].rsplit(':',1))
            date = datetime.strptime(date,'%Y-%m-%dT%H:%M:%S%z')
            mov['date'] = date
            mov['change'] = rmov['change']
            mov['currency'] = rmov['currency']
            mov['description'] = rmov['description']
            mov['type'] = rmov['type']
            if 'orderId' in rmov:
                 mov['orderId'] = rmov['orderId']
            if 'productId' in rmov:
                 mov['productId'] = rmov['productId']
            movs.append(mov)        
        return movs

    # Returns historical transactions
    #  fromDate and toDate are strings in the format: dd/mm/yyyy
    def getTransactions(self, fromDate, toDate):
        url = 'https://trader.degiro.nl/reporting/secure/v4/transactions'
        payload = {'fromDate': fromDate,
                   'toDate': toDate,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get Transactions overview')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()['data']
        return data

    # Returns product info 
    #  ids is a list of product ID (from Degiro)
    def getProductByIds(self, ids):
        url = "https://trader.degiro.nl/product_search/secure/v5/products/info"
        header = {'content-type': 'application/json'}
        params = {'intAccount': str(self.user['intAccount']), 'sessionId': self.sessid}
        r = self.sess.post(url, headers=header, params=params, data=json.dumps([str(id) for id in ids]))

        print(f'Get Products info for {ids}')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()['data']
        return data


if __name__ =='__main__':
    deg = degiro()
    deg.login(with2fa=True)
