import requests
import json

class degiro:
    def __init__(self):
        self.user = dict()
        self.data = None
    
    def login(self, conf_path):
        conf = json.load(open(conf_path))
        self.sess = requests.Session()
        
        # Login
        url = 'https://trader.degiro.nl/login/secure/login'
        payload = {'username': conf['username'],
                   'password': conf['password'],
                   'isPassCodeReset': False,
                   'isRedirectToMobile': False}
        header={'content-type': 'application/json'}

        r = self.sess.post(url, data=json.dumps(payload))
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
        self.user['intAccount'] = data['intAccount']
        
        print('\tAccount id: {}'.format(self.user['intAccount']))
        
    # This gets a lot of data, orders, news, portfolio, currencies etc.
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
    
    # Only returns a summary of the portfolio
    def getPortfolioSummary(self):
        if self.data == None:
            self.getData()
        resv = dict()
        for v in self.data['totalPortfolio']['value']:
            resv[v['name']] = v['value']

        pfSummary = dict()
        pfSummary['equity'] = resv['portVal']
        pfSummary['cash'] = resv['cash']
        pfSummary['total'] = resv['total']
        return pfSummary
    
    # Returns the entire portfolio
    def getPortfolio(self):
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
        return portfolio
