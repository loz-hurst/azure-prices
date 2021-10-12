#!/usr/bin/env python

# Core libraries
import argparse
import logging

# 3rd party libraries
import requests


logger = logging.getLogger(__name__)

class AzurePricesApiError(RuntimeError):
    pass

def _do_prices_api_call(url_arguments):
    """
    Calls the Azure API with a load of boilerplate checks.

    Args:
        url_arguments - string arument to append to the url

    Returns:
        python object from json-decoding the response

    Raises:
        AzurePricesApiError if an error occurrs calling the api
    """
    method_log = logger.getChild('call_api')

    method_log.debug("Calling Azure API")

    result = requests.get("https://prices.azure.com/api/retail/prices?%s" % url_arguments)

    if result.status_code != 200:
        message = "Non-zero exit code (%d) from api call.  Response body was: %s" % (result.status_code, result.text)
        method_log.error(message)
        raise AzurePricesApiError(message)

    json_result = result.json()
    # Sanity check
    if json_result['Count'] != len(json_result['Items']):
        method_log.warning("Azure API call did not return the number of items (%d) it said it found (%d)", len(json_result['Items']), json_result['Count'])

    return json_result

def get_azure_prices(skus, currency='GBP'):
    """
    Call the Azure Prices API and return a dict of current prices for the give skuIds.

    Arguments:
        skus - iterable yielding list of skus as strings
        currency - a supported currency (see: https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#supported-currencies)
                   to query the API for.  Defaults to GBP.

    Returns:
        dict of skus mapped to prices
    """
    method_log = logger.getChild('call_api')

    result = _do_prices_api_call("currencyCode='%s'&$filter=%s" % (currency, ' or '.join(["skuId eq '%s'" % x for x in skus])))

    # Sanity check
    if result['Count'] != len(skus):
        method_log.warning("Azure API call did not return the same number of skus (%d) as was requested (%d)", result['Count'], len(skus))
    print(result)


def find_azure_skus_by_armSkuName(armSkuNames):
    """
    Find a print brief summary of Skus from the armSkuName

    Arguments:
        armSkuNames - iterable yeilding a list of armSkuNames to search for.

    Returns:
        Nothing
    """
    method_log = logger.getChild('call_api')

    method_log.debug("Calling Azure API")
    
    result = _do_prices_api_call("$filter=%s" % ' or '.join(["armSkuName eq '%s'" % x for x in armSkuNames]))
    # Sanity check
    if result['Count'] < len(armSkuNames):
        method_log.warning("Azure API call did not return at least the number of armSkuName results (%d) as was requested (%d)", result['Count'], len(armSkuNames))

    print("skuId             type               region         armSkuName skuName")
    for item in result['Items']:
        print("%(skuId)-17s %(type)-18s %(armRegionName)-14s %(armSkuName)s %(skuName)s" % item)


# Being run as a script?
if __name__ == '__main__':
    log_levels = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR, 'critical': logging.CRITICAL, 'none': None}

    # Process command-line options
    parser = argparse.ArgumentParser(description='Azure price getter.')
    parser.add_argument('--log-level', '-l', choices=log_levels.keys(), default='info', help="Logging output level (default: info)")
    parser.add_argument('--prefix', action='store_true', help="Prefix log messages with their level")
    parser.add_argument('--find-armSkuName', action='append', help="Find a list of all matching entries by armSkuName (e.g. Standard_HC44rs) and list them")

    args = parser.parse_args()

    # Setup logging
    if log_levels[args.log_level] is not None:
        fmt_normal="%(name)s: %(message)s"
        fmt_prefix="[ %(levelname)-8s ] %(name)s: %(message)s"

        logging.basicConfig(level=log_levels[args.log_level], format=fmt_prefix if args.prefix else fmt_normal)

    # Search for skus, if requested
    if args.find_armSkuName:
        find_azure_skus_by_armSkuName(args.find_armSkuName)

    # Get requested prices
    #get_azure_prices(['DZH318Z0BXNX/000G']) # HC44rs
    get_azure_prices(['DZH318Z0BXNH/0002'])
    logger.debug("Finished.")
