#!/usr/bin/env python

# Copyright 2021 Laurence Alexander Hurst
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Core libraries
import argparse
from collections import defaultdict
from enum import Enum, auto
import inspect
import json
import logging
import sys

# 3rd party libraries
import requests
from tabulate import tabulate

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

def _build_filter(filter):
    """
    Build a filter for the Azure API.

    Args:
        filter - dict of properties to iterable of wanted values

    Returns:
        A string containing the built filter, suitable for passing to the $filter URL parameter of the Azure price API call
    """
    if not filter:
        # No restriction required, we are done.
        return ''
    method_log = logger.getChild('_build_filter')
    
    built_filter=""
    for key, values in filter.items():
        method_log.debug("Adding filter for %s, values %s", key, values)
        if built_filter:
            built_filter += " and "
        built_filter += "(%s eq '%s')" % (key, ("' or %s eq '" % key).join(values))


    method_log.debug("Built filter: %s", built_filter)
    return built_filter

def get_azure_prices(limit, currency='GBP'):
    """
    Call the Azure Prices API and return a dict of current prices for the give skuIds.

    Arguments:
        limit - dict of properties to iterable of desired values to limit the search to
        currency - a supported currency (see: https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices#supported-currencies)
                   to query the API for.  Defaults to GBP.

    Returns:
        dict of skuIds mapped to list of found items for that skuId
    """
    method_log = logger.getChild('get_azure_prices')

    api_args = "currencyCode='%s'" % currency
    filter = _build_filter(limit)
    if filter:
        api_args += "&$filter=%s" % filter

    result_items = []
    next_page = True
    while next_page:
        result = _do_prices_api_call(api_args)
        result_items.extend(result['Items'])
        next_page = result['NextPageLink']  # None evaluates to False
        if next_page:
            api_args = next_page.split('?', 1)[1]
            method_log.debug("Next page of results detected.  URI: %s, args: %s", next_page, api_args)


    method_log.info("%d items found from Azure Prices API", len(result_items))

    # Transform to a skuId orientated list
    sku_items = defaultdict(list)
    for item in result_items:
        sku_items[item['skuId']].append(item)
    method_log.info("%d discrete skuIds found from Azure Prices API", len(sku_items))
    return result_items

def find_outputters():
    """
    Find a list of all available output methods.

    Returns:
    dict of name of output method mapped to the method that implements it.
    """
    result = {}
    prefix = "output_"

    for potential_method in inspect.getmembers(sys.modules[__name__]):
        if potential_method[0].startswith(prefix):
            try:
                method_name = potential_method[1].user_facing_name
            except AttributeError:
                method_name = potential_method[0][len(prefix):]
            result[method_name] = potential_method[1]

    return result

def output_table(data, select=None):
    """
    Output data in a human-readable table.

    Args:
        data: dict of data to output.
        select: optional list of keys to output (will output everything if no list provided)

    Returns: nothing
    """
    if select:
        output_keys = select
    else:
        output_keys = data.keys()
    print(tabulate([[x[y] for y in output_keys] for x in data], headers=output_keys))

def output_csv(data, select=None):
    """
    Output data as comma-seperated values.

    Args:
        data: dict of data to output.
        select: optional list of keys to output (will output everything if no list provided)

    Returns: nothing
    """
    if select:
        output_keys = select
    else:
        output_keys = data.keys()
    print('"' + '","'.join(output_keys) + '"') # Header row
    print("\n".join(['"' + '","'.join([str(x[y]) for y in output_keys]) + '"' for x in data]))

def output_tsv(data, select=None):
    """
    Output data as tab-seperated values.

    Args:
        data: dict of data to output.
        select: optional list of keys to output (will output everything if no list provided)

    Returns: nothing
    """
    if select:
        output_keys = select
    else:
        output_keys = data.keys()
    print("\t".join(output_keys)) # Header row
    print("\n".join(["\t".join([str(x[y]) for y in output_keys]) for x in data]))

def output_json(data, select=None):
    """
    Output data as a JSON list.

    Args:
        data: dict of data to output.
        select: optional list of keys to output (will output everything if no list provided)

    Returns: nothing
    """
    if select:
        output_keys = select
    else:
        output_keys = data.keys()
    print(json.dumps([{y: x[y] for y in output_keys} for x in data]))

# Being run as a script?
if __name__ == '__main__':
    log_levels = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR, 'critical': logging.CRITICAL, 'none': None}

    docs_url = "https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices"

    outputters = find_outputters()

    # Process command-line options
    parser = argparse.ArgumentParser(description='Azure price API tool.')
    parser.add_argument('--log-level', '-l', choices=log_levels.keys(), default='info', help="Logging output level (default: info)")
    parser.add_argument('--prefix', action='store_true', help="Prefix log messages with their level")
    parser.add_argument('--format', choices=outputters.keys(), default='table', help="Output format (defaults to table)")
    parser.add_argument('--select', metavar='property', action='append', help="Properties to output (see %s for available options)" % docs_url)
    parser.add_argument('--limit', nargs=2, metavar=('property', 'value'), action='append', help="Limit search by property values (repeated values for the same property will be 'OR'd together, properties will be 'AND'd) (see %s for available options)" % docs_url)

    args = parser.parse_args()

    # Setup logging
    if log_levels[args.log_level] is not None:
        fmt_normal="%(name)s: %(message)s"
        fmt_prefix="[ %(levelname)-8s ] %(name)s: %(message)s"

        logging.basicConfig(level=log_levels[args.log_level], format=fmt_prefix if args.prefix else fmt_normal)

    limit_dict = defaultdict(list)
    for (property_, value) in args.limit if args.limit else []:
        limit_dict[property_].append(value)

    # Get requested prices
    outputters[args.format](get_azure_prices(limit_dict), args.select)

    logger.debug("Finished.")

