#!/usr/bin/python 2.7.11
import settings #simple settings file for AUTH, added to gitignore
import requests
import json, ast
import sys
import pprint
import iso8601
import klaviyo
import base64
from datetime import datetime, timedelta
#<=========================== Global Variables and Auth ====================>
# Settings file allows interchanging of store, URL, and Auth.
KLAVIYO_KEY = settings.klaviyo_key
SHOPIFY_KEY = settings.shopify_api_key
SHOPIFY_PW = settings.shopify_password
SHOPIFY_URL = settings.shopify_url
SHOPIFY_PATH = settings.shopify_path
#Variables to allow for date filtering of orders by date.
START_DATE = '2016-01-01T00:00:00-04:00'
END_DATE = '2016-12-31T00:00:00-04:00'
#list to indicate what financial_status to filter. This way, we can add whatever statuses for which want to filter. I operated on the assumption that 'paid' was the status that meant the order is complete, after referring to the shopify docs. However, the script will work either way.
ORDER_STATUS = ['paid']
# just some abbreviation for pretty print
p = pprint
#<=========================== Main Functions ===============================>
def main():
    #function to handle timestamp conversion, from Datetime to Unix to be able to pass unix time to Klaviyo as per instructions.
    def convert_to_unix(dt):
        assert dt.tzinfo is not None and dt.utcoffset() is not None
        utc_naive  = dt.replace(tzinfo=None) - dt.utcoffset()
        timestamp = (utc_naive - datetime(1970, 1, 1)).total_seconds()
        return timestamp
    #get all orders from shopify
    def get_orders():
        #create empty list to push order data to.
        order_object = []
        #order_count so that I can check the number of orders that evaluate to True from the if statement on line 58 (For QA Purposes)
        order_count = 0
        #create URL variable, format with global variables.
        url = ('https://{}:{}@{}{}'.format(SHOPIFY_KEY, SHOPIFY_PW, SHOPIFY_URL, SHOPIFY_PATH))
        #just some general error handling for QA
        try:
            response = requests.get(url)
            #verify the server response
            if response.status_code == 200:
                orders = response.json()['orders']
                #print pretty print formatted orders to make it easier to identify key json properties (for QA Purposes)
                p.pprint(orders)
                #iterate through items in the orders object returned by endpoint
                for item in orders:
                    #create if statement to evaluate if the orders financial_status == 'paid'(this can be ) and that the
                    #date range is correct for 2016
                    #It was unclear what constituted the date of the order, so I used ['created_at']. However, this can easily be swapped out with ['updated_at'] or ['processed_at'] by just swapping out the property in 4 spots.
                    if item['created_at'] > START_DATE and item['created_at'] < END_DATE and item['financial_status'] in ORDER_STATUS:
                        #increment order counter for testing and QA
                        order_count+=1
                        #print paid status, Date Ordered, Email, order count for QA
                        # print 'Paid Status: {} | Date Ordered: {} | Email: {} | Order Count: {}'.format(item['financial_status'],item['updated_at'], item['email'], order_count)
                        #append item to order_object if it evaluates to True
                        order_object.append(item)
            else:
                return {}
        #raise general exception for any error.
        except:
            e = sys.exc_info(0)
            print e
        #return order_object to pass to send_data
        return order_object
    #function to make the http requests through the Klaviyo Python library.
    def send_data(orders):
        url = ('https://a.klaviyo.com/api/track')
        #iterate through items in orders to append data and make Placed Order Calls.
        # In the case that there is more than one order, this allows me to add each one to properties['items'].
        for item in orders:
            #lists to populate with data so it can be passed to the 'properties' parameter.
            #scoped inside loop so it clears out once the loop iterates, allowing it to build from scratch each time.
            items = []
            item_names = []
            #iteratare through line_items from orders and append to items list
            for lineItem in item['line_items']:
                items.append({'SKU': lineItem['sku'],
                             'Name' : lineItem['name'],
                             'Quantity' : lineItem['quantity'],
                             'ItemPrice' : lineItem['price'],
                             'RowTotal': lineItem['quantity']*lineItem['price']
                             })
                #build list of item names to pass to Placed Order call, in the event there is more than one line item
                item_names.append(lineItem['name'])
                #since we're already iterating through line_items, set up and make the track calls for 'Ordered Product'
                #build ordered_data object.
                ordered_data = {
                    'token' : KLAVIYO_KEY,
                    'event' : 'Ordered Product',
                    'customer_properties' : {
                        '$email' : item['email'],
                        '$first_name' : item['customer']['first_name'],
                        '$last_name' : item['customer']['last_name']
                    },
                    'properties': {
                        'Type' : 'Shopify Backfill',
                        '$event_id' : '{}_{}'.format(item['id'], lineItem['name']),
                        '$value' : item['total_price_usd'],
                        'Name' : lineItem['name'],
                        'Quantity' : lineItem['quantity']
                    },
                    'time' : int(convert_to_unix(iso8601.parse_date(item['created_at'])))
                }
                #use json.dumps to properly format json string before base64 encoding.
                ordered_data = json.dumps(ordered_data)
                #make call for the Ordered Product
                response = requests.get(url, params={'data': base64.urlsafe_b64encode(str(ordered_data))})
                print response.content
            #quick and dirty hack to remove unicode 'u's from list for readability in Klaviyo.
            items = [ast.literal_eval(json.dumps(items))]
            #make Placed Order call for each item in orders
            placedOrder_data = {
                'token' : KLAVIYO_KEY,
                'event' : 'Placed Order',
                'customer_properties' : {
                    '$email' : item['email'],
                    '$first_name' : item['customer']['first_name'],
                    '$last_name' : item['customer']['last_name']
                    },
                    'properties' : {
                        'Type': 'Shopify Backfill',
                        '$event_id' : item['id'],
                        '$value' : item['total_price_usd'],
                        'ItemNames' : item_names,
                        'Discount Code' : item['discount_codes'],
                        'Discount Value' : item['total_discounts'],
                        'Items' : items, #each item from line item will be
                    },
                    'time' : int(convert_to_unix(iso8601.parse_date(item['created_at'])))
            }
            #use json.dumps to properly format json string before base64 encoding.
            placedOrder_data = json.dumps(placedOrder_data)
            resp = requests.get(url, params={'data':base64.urlsafe_b64encode(str(placedOrder_data))})
            print resp.content
    #call functions
    send_data(get_orders())
#call main function
if __name__ == '__main__':
    main()
