# shopify-backfill

I started off using the server side Python library, which was great, but ran into trouble while trying to add the time of the order so that it displayed properly on the profile's timeline. There didn't seem to be an appropriate parameter. I then switched to using the python requests library and encoding the data in base64 prior to making the call. 

After reading through the Shopify documentation, I came to the conclusion that only orders with the 'financial_status == 'paid' counted as completed orders. Though, I did set the script up so that multiple statuses can be passed in if desired. As for the date of the order, I used 'created_at'. However, this can be swapped out for 'updated_at' or 'processed_at'.

I used Python 2.7.11 and used a virtual environment. To run the script, simply install the requirements and swap in your own API key in the settings file. 


