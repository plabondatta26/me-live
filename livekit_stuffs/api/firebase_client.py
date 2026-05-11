from pathlib import Path
import firebase_admin
from firebase_admin import firestore,credentials, messaging

class FirebaseClient:

    def __init__(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            BASE_DIR = Path(__file__).resolve().parent.parent

            path = Path.joinpath(BASE_DIR, "api/me-live-620bf-firebase-adminsdk-u1urz-868d04f265.json")
            cred = credentials.Certificate(path)

            firebase_admin.initialize_app(cred)
            # firebase_admin.initialize_app(
            #     credentials.Certificate(settings.FIREBASE_ADMIN_CERT)
            # )

        self.firestore_db = firestore.client()
        # self.messaging = messaging._get_messaging_service(firebase_admin.get_app())
        # self.messaging = messaging


        # self._db = firestore.client()
        # self._collection = self._db.collection(u'todos')

    def send_single_fcm(self,registration_token,data): 
        # This registration token comes from the client FCM SDKs.

        # See documentation on defining a message payload.
        message = messaging.Message(
            notification= messaging.Notification(title=data['title'],body=data['message'],),
            # data={"title":"title","message":"message"},
            data=data,
            token=registration_token,
        )

        # Send a message to the device corresponding to the provided
        # registration token.
        messaging.send(message)
        # Response is a message ID string.
        # print('Successfully sent message:', response)

    def send_multicast_fcm(self,registration_tokens, data):
        # # Create a list containing up to 500 registration tokens.
        # # These registration tokens come from the client FCM SDKs.
        # registration_tokens = [
        #     'YOUR_REGISTRATION_TOKEN_1',
        #     # ...
        #     'YOUR_REGISTRATION_TOKEN_N',
        # ]

        message = messaging.MulticastMessage(
            notification= messaging.Notification(title=data['title'],body=data['message'],),
            data=data,
            tokens=registration_tokens,
        )
        response = messaging.send_each_for_multicast(multicast_message=message)
        # See the BatchResponse reference documentation
        # for the contents of response.
        # print('{0} messages were sent successfully'.format(response.success_count))


    # def send_single_fcm(self,message):
    #     print('Testing...............................................')
    #     '''
    #     def __init__(self, data=None, notification=None, android=None, webpush=None, apns=None,
    #              fcm_options=None, token=None, topic=None, condition=None):
    #     self.data = data
    #     self.notification = notification
    #     self.android = android
    #     self.webpush = webpush
    #     self.apns = apns
    #     self.fcm_options = fcm_options
    #     self.token = token
    #     self.topic = topic
    #     self.condition = condition
    #     '''

    #     try:
    #         self.messaging.send(message)
    #     except:
    #         print("Failed.................................")

    # def create(self, data):
    #     """Create todo in firestore database"""
    #     doc_ref = self._collection.document()
    #     doc_ref.set(data)

    # def update(self, id, data):
    #     """Update todo on firestore database using document id"""
    #     doc_ref = self._collection.document(id)
    #     doc_ref.update(data)

    # def delete_by_id(self, id):
    #     """Delete todo on firestore database using document id"""
    #     self._collection.document(id).delete()

    # def get_by_id(self, id):
    #     """Get todo on firestore database using document id"""
    #     doc_ref = self._collection.document(id)
    #     doc = doc_ref.get()

    #     if doc.exists:
    #         return {**doc.to_dict(), "id": doc.id}
    #     return

    # def all(self):
    #     """Get all todo from firestore database"""
    #     docs = self._collection.stream()
    #     return [{**doc.to_dict(), "id": doc.id} for doc in docs]

    # def filter(self, field, condition, value):
    #     """Filter todo using conditions on firestore database"""
    #     docs = self._collection.where(field, condition, value).stream()
    #     return [{**doc.to_dict(), "id": doc.id} for doc in docs]
