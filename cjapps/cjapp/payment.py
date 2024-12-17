import razorpay
from django.conf import settings

class RzpClient():
    def __init__(self, *args, **kwargs):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        self.client.set_app_details({"title" : settings.RAZORPAY_APP_TITLE, "version" : settings.RAZORPAY_APP_VERSION})

    def createOrder(self, data={}):
        # data = { "amount": 500, "currency": "INR", "receipt": "order_rcptid_11" }
        # if data is None:
        #     data = { "amount": (amount*100), "currency": currency, "receipt": receipt }

        return self.client.order.create(data=data)
        

    def verifyPayment(self, options={}):
        # generated_signature = hmac_sha256(order_id + "|" + razorpay_payment_id, secret);

        generated_signature = self.client.utility.verify_payment_signature(options)

        return generated_signature #True if (generated_signature == razorpay_signature) else False
        