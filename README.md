# Script(s) to fetch Azure prices using the Azure Price API

The Azure price API documentation can be found at <https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices>

## Reqirement

* Python 3.4
* [Python Requests](https://docs.python-requests.org/)
* [tabulate](https://github.com/astanin/python-tabulate)

## Download and use

The best way is to create a VirtualEnv containing the requirements for this tool.

1. Create and activate your virtualenv in the usual way.
2. From the downloaded source, install the requirements:
  pip install -r requirements.txt
3. Run the script:
  python3 azure-prices.py

By default, the tool will display a selection of SKUs relevant to the developer's environment on STDOUT.  Try running with `--help` to see the options to modify this behaviour.


## Examples

Get the sku IDs, price type, name (arm), name (human), region, retail (undiscounted) price and unit price for for consumption prices for HC44 and HB60 type nodes in west europe:

```
azure-prices.py --limit armSkuName Standard_HC44rs --limit armSkuName Standard_HB60rs --limit armRegionName westeurope --limit priceType Consumption --select skuId --select type --select armSkuName --select skuName --select armRegionName --select retailPrice --select unitPrice
```

