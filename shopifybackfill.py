
import settings #simple settings file to use for AUTH added to gitignore to keep variables secret.
import requests
import json
import sys
import pprint
from datetime import datetime, timedelta
import iso8601
import klaviyo


#<=========================== Global Variables and Auth ====================>
# Settings file allows interchanging of store, URL, and Auth.
KLAVIYO_KEY = settings.klaviyo_key
SHOPIFY_KEY = settings.shopify_api_key
SHOPIFY_PW = settings.shopify_password
SHOPIFY_URL = settings.shopify_url
SHOPIFY_PATH = settings.shopify_path
#add KLAVIYO_KEY for use with KLAVIYO Python Library.
client = klaviyo.Klaviyo(KLAVIYO_KEY)
p = pprint

#Variables to allow for date filtering of orders.
START_DATE = '2016-01-01T00:00:00-04:00'
END_DATE = '2016-12-31T00:00:00-04:00'

def main():
    #function to handle timestamp conversion, from Datetime to Unix to be able to pass unix time to Klaviyo.
    def convert_to_unix(dt):

        assert dt.tzinfo is not None and dt.utcoffset() is not None
        utc_naive  = dt.replace(tzinfo=None) - dt.utcoffset()
        timestamp = (utc_naive - datetime(1970, 1, 1)).total_seconds()

        return timestamp

    #get all orders from shopify
    def get_orders():
        #create empty list to push order data to.
        order_object = []
        #order_count so that I can check the number of orders that evaluate to True from the if statement on line 58
        order_count = 0
        #create URL variable, format with global variables.
        url = ('https://{}:{}@{}{}'.format(SHOPIFY_KEY, SHOPIFY_PW, SHOPIFY_URL, SHOPIFY_PATH))
        #add in some basic error handling
        try:
            response = requests.get(url)
            orders = response.json()['orders']
            #print pretty print formatted orders to make it easier to identify key json properties.
            p.pprint(orders)

            #iterate through items in the orders object returned by endpoint
            for item in orders:
                #create if statement to evaluate if the orders financial_statues == 'paid' and that the date range is correct for 2016
                if item['updated_at'] > START_DATE and item['updated_at'] < END_DATE and item['financial_status'] == 'paid':
                    order_count+=1
                    #print date ranges and
                    print 'Paid Status: {} | Date Ordered: {} | Email: {} | Order Count: {}'.format( item['financial_status'], item['updated_at'], item['email'], order_count)
                    order_object.append(item)

        except:
            e = sys.exc_info()
            print e
            print response.text


        return order_object

    #function to make the http requests through the Klaviyo Python library.
    def send_data(orders):

        #iterate through items in orders to append data and make Placed Order Calls.
        # In the case that there is more than one order, this allows me to add each one to properties['items'].
        for item in orders:
            #lists to populate with data so it can be passed to the 'properties' parameter.
            #scoped inside loop so it clears out once the loop iterates, allowing it to build from scratch each time.
            items = []
            item_names = []

            for lineItem in item['line_items']:
                items.append({'SKU': lineItem['sku'].encode('utf-8'),
                             'Name' : lineItem['name'].encode('utf-8'),
                             'Quantity' : lineItem['quantity'],
                             'ItemPrice' : lineItem['price'].encode('utf-8'),
                             'RowTotal': lineItem['quantity']*lineItem['price']
                             })
                item_names.append(lineItem['name'])

                client.track('Ordered Product', email=item['email'],
                         customer_properties={
                            '$first_name' : item['customer']['first_name'],
                            '$last_name' : item['customer']['last_name']},
                        properties={
                            '$event_id' : '{}_{}'.format(item['id'], lineItem['name']),
                            '$value' : item['total_price_usd'],
                            'Name': lineItem['name'],
                            'Quantity': lineItem['quantity'],
                            'time': convert_to_unix(iso8601.parse_date(item['processed_at']))
                        })

            #make Placed Order call for each item in orders
            client.track('Placed Order', email=item['email'],
                         customer_properties={
                            '$first_name' : item['customer']['first_name'],
                            '$last_name' : item['customer']['last_name']},
                        properties={
                            '$event_id' : item['id'],
                            '$value' : item['total_price_usd'],
                            'ItemNames': item_names,
                            'Discount Code': item['discount_codes'],
                            'Discount Value': item['total_discounts'],
                            'Items' : items, #each item from line item will be here.
                            'time': convert_to_unix(iso8601.parse_date(item['processed_at']))
                        })



    send_data(get_orders())

if __name__ == '__main__':
    main()





