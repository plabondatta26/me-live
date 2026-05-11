import json
from celery import shared_task
from django.utils import timezone
from websocket import create_connection
from accounts.models import User
from profiles.models import Profile
from balance.models import Contribution
from tracking.models import GiftSendVatDiamonds
from me_live.utils.constants import liveRoomSocketBaseUrl
# from livekit_stuffs.api.constants import firestore_db

@shared_task
def gifting_execution(sender_uid,receiver_uid,diamonds,vat):
    # user_obj = User.objects.filter(id=int(sender_uid)).select_related('profile').first()
    # receiver_user_obj = User.objects.filter(id=int(receiver_uid)).select_related('profile').first()
    profile_obj = Profile.objects.filter(user__id=int(sender_uid)).select_related('user').only('diamonds','outgoing_diamonds','user__id').first()
    receiver_profile_obj = Profile.objects.filter(user__id=int(receiver_uid)).select_related('user').only('diamonds','user__id').first()


    # if user_obj and receiver_user_obj:
    if profile_obj and receiver_profile_obj:
        # profile_obj = user_obj.profile
        if profile_obj.diamonds >= diamonds:
            user_obj = profile_obj.user
            receiver_user_obj = receiver_profile_obj.user
            
            # Sender diamonds
            profile_obj.diamonds -= diamonds
            try:
                profile_obj.outgoing_diamonds += diamonds - vat
            except:
                pass

            profile_obj.save(force_update=True) 

            # Receiver diamonds
            # receiver_uid is the ID of receiver user
            # receiver_profile_obj = receiver_user_obj.profile
            receiver_profile_obj.diamonds += diamonds - vat
            receiver_profile_obj.save(force_update=True)

            # earning_history_obj = EarningHistory()
            # earning_history_obj.user = receiver_user_obj 
            # earning_history_obj.gift_sender = user
            # earning_history_obj.diamonds = int(diamonds)

            # earning_history_obj.save()

            gift_send_vat_diamonds_obj = GiftSendVatDiamonds.objects.first()
            if gift_send_vat_diamonds_obj is None:
                gift_send_vat_diamonds_obj = GiftSendVatDiamonds()
                gift_send_vat_diamonds_obj.gift_vat_diamonds = vat
                gift_send_vat_diamonds_obj.save(force_insert=True)
            else:
                gift_send_vat_diamonds_obj.gift_vat_diamonds += vat
                gift_send_vat_diamonds_obj.save(force_update=True)

            # Contribution
            contribution_obj = Contribution.objects.filter(user=receiver_user_obj,contributor=user_obj).first() 
            if contribution_obj is None:
                contribution_obj = Contribution()
                contribution_obj.user = receiver_user_obj
                contribution_obj.contributor = user_obj
                contribution_obj.diamonds = diamonds - vat
                contribution_obj.datetime = timezone.now()
                contribution_obj.save(force_insert=True)
            else:
                # Update coins contribution
                contribution_obj.diamonds += diamonds - vat
                contribution_obj.datetime = timezone.now()
                contribution_obj.save(force_update=True) 

            # # Websocket
            # live_data = {
            #     "type": "update_diamonds",
            #     "channelName": f"{receiver_uid}",
            #     'diamonds':receiver_profile_obj.diamonds
            # }

            # channel_layer = get_channel_layer()
           
            # async_to_sync(channel_layer.group_send)(
            #     f'live_streaming_livekit_streamings',
            #     {
            #         'type': 'live_streaming', 
            #         'message': live_data
            #     }
            # )

            # # Firebase
            # firebase_client = FirebaseClient()
            # db_ref = firebase_client.firestore_db.collection("LiveRoom").document(f"{receiver_uid}")
            # doc = db_ref.get()
            
            # if doc.exists:
            #     firestore_json_data = doc.to_dict()
            #     try:
            #         update_data = {
            #             "diamonds":  firestore_json_data["diamonds"] + diamonds - vat
            #         }
            #         db_ref.update(update_data)
            #     except:
            #         pass

        
        return 'executing gifting'
    
@shared_task
def paying_live_lock_diamonds(host_id,group_callers):
    host_profile_obj = Profile.objects.filter(user__id=host_id).first()
    if host_profile_obj:
        paying_diamonds = 200
        gain_diamonds = 100
        vat_diamonds = 100
        total_vat_diamonds = 0
        
        for group_caller in group_callers:
            if group_caller['uid'] != host_id:
                caller_user_obj = User.objects.filter(id=group_caller['uid']).first()
                if caller_user_obj:
                    # Take action
                    caller_profile_obj = caller_user_obj.profile
                    if caller_profile_obj.diamonds >= paying_diamonds:
                        caller_profile_obj.diamonds -= paying_diamonds
                        caller_profile_obj.save()

                        host_profile_obj.diamonds += gain_diamonds
                        host_profile_obj.save()
                        total_vat_diamonds += vat_diamonds

                        caller_data = {
                            "action": 'paying_live_lock',
                            "uid": group_caller['uid'],
                            "allow": True,
                            "diamonds": -paying_diamonds,
                        }
                        host_data = {
                            "action": 'paying_live_lock',
                            "uid": host_id,
                            "allow": True,
                            "diamonds": gain_diamonds,
                        }

            
                        # async_to_sync(channel_layer.group_send)(
                        #     f'live_room_{host_id}',
                        #     {
                        #         'type': 'live_room',  
                        #         'message': caller_data
                        #     }
                        # )
                        # async_to_sync(channel_layer.group_send)(
                        #     f'live_room_{host_id}',
                        #     {
                        #         'type': 'live_room',  
                        #         'message': host_data
                        #     }
                        # )
                        # External websocket
                        ws = create_connection(f"{liveRoomSocketBaseUrl}/{host_id}/")
                        ws.send(json.dumps({"message": caller_data}))
                        ws.send(json.dumps({"message": host_data}))
                        ws.close()

                    else:
                        disallowed_data = {
                            "action": 'paying_live_lock',
                            "uid": group_caller['uid'],
                            "allow": False,
                            "diamonds": 0,
                        }
                        # async_to_sync(channel_layer.group_send)(
                        #     f'live_room_{host_id}',
                        #     {
                        #         'type': 'live_room',  
                        #         'message': disallowed_data
                        #     }
                        # )
                        # External websocket
                        ws = create_connection(f"{liveRoomSocketBaseUrl}/{host_id}/")
                        ws.send(json.dumps({"message": disallowed_data}))
                        ws.close()

        gift_send_vat_diamonds_obj = GiftSendVatDiamonds.objects.first()
        if gift_send_vat_diamonds_obj is None:
            gift_send_vat_diamonds_obj = GiftSendVatDiamonds()
            gift_send_vat_diamonds_obj.live_lock_vat_diamonds = total_vat_diamonds
        else:
            gift_send_vat_diamonds_obj.live_lock_vat_diamonds += total_vat_diamonds
        gift_send_vat_diamonds_obj.save()
    return 'paying_live_lock_diamonds is processing'

@shared_task
def paying_call_lock_diamonds(host_id,uid,paying_diamonds):
    host_profile_obj = Profile.objects.filter(user__id=host_id).first()
    if host_profile_obj:
        
        caller_profile_obj = Profile.objects.filter(user__id=uid).first()
        if caller_profile_obj:
            if caller_profile_obj.diamonds >= paying_diamonds:
                caller_profile_obj.diamonds -= paying_diamonds
                caller_profile_obj.save(force_update=True)

                host_profile_obj.diamonds += paying_diamonds
                host_profile_obj.save(force_update=True)

                # Decrease
                caller_data = {
                    "action": 'paying_call_lock',
                    "uid":uid,
                    "allow": True,
                    "diamonds": -paying_diamonds,
                }
                # Increase
                host_data = {
                    "action": 'paying_call_lock',
                    "uid": host_id,
                    "allow": True,
                    "diamonds": paying_diamonds,
                }


                # async_to_sync(channel_layer.group_send)(
                #     f'live_room_{host_id}',
                #     {
                #         'type': 'live_room',  
                #         'message': caller_data
                #     }
                # )
                # async_to_sync(channel_layer.group_send)(
                #     f'live_room_{host_id}',
                #     {
                #         'type': 'live_room',  
                #         'message': host_data
                #     }
                # )
                # External websocket
                ws = create_connection(f"{liveRoomSocketBaseUrl}/{host_id}/")
                ws.send(json.dumps({"message": caller_data}))
                ws.send(json.dumps({"message": host_data}))
                ws.close()

            else:
                disallowed_data = {
                    "action": 'paying_call_lock',
                    "uid": uid,
                    "allow": False,
                    "diamonds": 0,
                }
                # async_to_sync(channel_layer.group_send)(
                #     f'live_room_{host_id}',
                #     {
                #         'type': 'live_room',  
                #         'message': disallowed_data
                #     }
                # )
                # External websocket
                ws = create_connection(f"{liveRoomSocketBaseUrl}/{host_id}/")
                ws.send(json.dumps({"message": disallowed_data}))
                ws.close()

    return 'paying_call_lock_diamonds is processing'
