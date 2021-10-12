# Script(s) to fetch Azure prices using the Azure Price API

The Azure price API documentation can be found at <https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices>

## Reqirement

* Python 3
* Python Requests

## Download and use

The best way is to create a VirtualEnv containing the requirements for this tool.

1. Create and activate your virtualenv in the usual way.
2. From the downloaded source, install the requirements:
  pip install -r requirements.txt
3. Run the script:
  python3 azure-prices.py

By default, the tool will display a selection of SKUs relevant to the developer's environment on STDOUT.  Try running with `--help` to see the options to modify this behaviour.


