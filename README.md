# Unofficial DeGIRO Python API
Very basic **unofficial** Python API for [DeGiro](https://www.degiro.nl). This API is only able to get details about your portfolio. It cannot be used for automatic trading. For a way more extensive Node.js API have a look at [pladarias](https://github.com/pladaria/degiro) work.

:warning: DeGiro could change their API at any moment, if something is not working, please open an issue.

## Security
Your password is stored plain text in a JSON file. Take adequate measures !, e.g. `chmod` it to `600`. The API also won't work for users who have 2FA enabled.

## Example usage
```python
from degiro import degiro

la = degiro()
la.login('config.json')
la.getConfig()
pfs = la.getPortfolioSummary()
portfolio = la.getPortfolio()
total = pfs['equity']

# Prints a pretty table of your equities and their allocation.
print('{:<20}\tsize\tvalue\tsubtot\t\talloc'.format('Product'))
for row in portfolio['PRODUCT'].values():
    subtot = row['size']*row['price']
    alloc = (subtot/total)*100 # Asset allocation (%)
    print('{:<20}\t{:5.1f}\t{:6.2f}\t{:7.2f}\t\t{:2.1f}%'.format(row['name'], row['size'], row['price'], subtot, alloc))
print('Total: {:.2f}'.format(total))
```
