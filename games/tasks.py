import json
import random
import threading
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from games.models import FortuneWheel, FortuneWheelPeriodicTracker
from games.api.serializers import FortuneWheelSerializer
from profiles.models import Profile
from tracking.models import GamesDiamonds
# celery -A me_live worker --beat --scheduler django --loglevel=info

# Fortune Wheel Game
@shared_task
def load_fortune_wheel_game():
    allow_perform = False
    fortune_wheel_obj = FortuneWheel.objects.first()
    if fortune_wheel_obj:
        fortune_wheel_tracker_obj = fortune_wheel_obj.fortune_wheel_tracker
        if fortune_wheel_tracker_obj.seconds < 46 and fortune_wheel_tracker_obj.repeats < 2:
            fortune_wheel_tracker_obj.repeats += 1
            fortune_wheel_tracker_obj.save(force_update=True)
        else:
            allow_perform = True
            fortune_wheel_obj.clear_fields()
    else:
        allow_perform = True
        fortune_wheel_obj = FortuneWheel()
        fortune_wheel_obj.save(force_insert=True)
        FortuneWheelPeriodicTracker.objects.create(game=fortune_wheel_obj)
    
    if allow_perform == True:
        global fortune_wheel_spinning, fortune_wheel_result_showing
        fortune_wheel_spinning = False
        fortune_wheel_result_showing = False
        WAIT_TIME_SECONDS = 1
        seconds = 1
        processing_fortune_wheel_game(seconds=seconds,fortune_wheel_obj=fortune_wheel_obj)

        ticker = threading.Event() 
        while not ticker.wait(WAIT_TIME_SECONDS):
            seconds += 1
            if seconds == 47:
                return
            processing_fortune_wheel_game(seconds=seconds,fortune_wheel_obj=fortune_wheel_obj)
        
    return 'spinning fortune wheel game is processing'

def processing_fortune_wheel_game(seconds,fortune_wheel_obj):
    global fortune_wheel_spinning, fortune_wheel_result_showing
    if seconds == 31:
        fortune_wheel_spinning = True
    elif seconds == 32:
        # Process calculation
        processing_fortune_wheel_game_result.delay()
    elif seconds == 42:
        fortune_wheel_spinning = False
        fortune_wheel_result_showing = True

    fortune_wheel_tracker_obj = fortune_wheel_obj.fortune_wheel_tracker
    fortune_wheel_tracker_obj.seconds = seconds
    fortune_wheel_tracker_obj.save(force_update=True)
    fortune_wheel_obj.refresh_from_db()
    serializer_fortune_wheel = FortuneWheelSerializer(instance=fortune_wheel_obj)
    data = {
        'type': 'game',
        'game_type': 'fortune_wheel',
        'spinning': fortune_wheel_spinning,
        'result_showing': fortune_wheel_result_showing,
        # 'seconds': fortune_wheel_seconds,
        'seconds': seconds,
        'winner_item': -1,
        'result': serializer_fortune_wheel.data,
    }
    channel_layer = get_channel_layer()
    # # TODO: Need to remove later
    # async_to_sync(channel_layer.group_send)(
    #     f'live_streaming_livekit_streamings',
    #     {'type': 'live_streaming', 'message': data}
    # )

    async_to_sync(channel_layer.group_send)(
        f'running_games_group',
        {'type': 'running_games', 'message': data}
    ) 

@shared_task
def processing_fortune_wheel_game_result():
    
    fortune_wheel_obj = FortuneWheel.objects.first()
    if fortune_wheel_obj:
        listItemValues = [
            'mango',
            'strawberry',
            'coconut',
            'apple',
            'cucumber',
            'pineapple',
          ]

        # Process
        min_item = ''
        total_played_diamonds = 0
        mango_total_winning_diamonds = fortune_wheel_obj.mango * fortune_wheel_obj.mango_times
        strawberry_total_winning_diamonds = fortune_wheel_obj.strawberry * fortune_wheel_obj.strawberry_times
        coconut_total_winning_diamonds = fortune_wheel_obj.coconut * fortune_wheel_obj.coconut_times
        apple_total_winning_diamonds = fortune_wheel_obj.apple * fortune_wheel_obj.apple_times
        cucumber_total_winning_diamonds = fortune_wheel_obj.cucumber * fortune_wheel_obj.cucumber_times
        pineapple_total_winning_diamonds = fortune_wheel_obj.pineapple * fortune_wheel_obj.pineapple_times

      
        times = 0
        choosers = []
        played_diamonds = "{}"
        winning_diamonds = 0

        item_indexes = [0,1,2,3,4,5]
        item_index = random.choice(item_indexes)
        min_item = listItemValues[item_index]
        fortune_wheel_obj.winner_index = item_index
        fortune_wheel_obj.save(force_update=True)
        fortune_wheel_obj.refresh_from_db()
        serializer_fortune_wheel = FortuneWheelSerializer(instance=fortune_wheel_obj)
        data = {
            'type': 'game',
            'game_type': 'fortune_wheel',
            'spinning': True,
            'result_showing': False,
            'seconds': 0,
            'winner_item': item_index,
            'result': serializer_fortune_wheel.data,
        }
        channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f'live_streaming_livekit_streamings',
        #     {'type': 'live_streaming', 'message': data}
        # )
        async_to_sync(channel_layer.group_send)(
            f'running_games_group',
            {'type': 'running_games', 'message': data}
        )

        if min_item == 'mango':
            times = fortune_wheel_obj.mango_times
            choosers = fortune_wheel_obj.mango_choosers.all()
            played_diamonds = fortune_wheel_obj.mango_played_diamonds
            winning_diamonds = mango_total_winning_diamonds
            

        elif  min_item == 'strawberry':
            times = fortune_wheel_obj.strawberry_times
            choosers = fortune_wheel_obj.strawberry_choosers.all()
            played_diamonds = fortune_wheel_obj.strawberry_played_diamonds
            winning_diamonds = strawberry_total_winning_diamonds


        elif min_item == 'coconut':
            times = fortune_wheel_obj.coconut_times
            choosers = fortune_wheel_obj.coconut_choosers.all()
            played_diamonds = fortune_wheel_obj.coconut_played_diamonds
            winning_diamonds = coconut_total_winning_diamonds

        elif min_item == 'apple':
            times = fortune_wheel_obj.apple_times
            choosers = fortune_wheel_obj.apple_choosers.all()
            played_diamonds = fortune_wheel_obj.apple_played_diamonds
            winning_diamonds = apple_total_winning_diamonds

        elif min_item == 'cucumber':
            times = fortune_wheel_obj.cucumber_times
            choosers = fortune_wheel_obj.cucumber_choosers.all()
            played_diamonds = fortune_wheel_obj.cucumber_played_diamonds
            winning_diamonds = cucumber_total_winning_diamonds

        elif min_item == 'pineapple':
            times = fortune_wheel_obj.pineapple_times
            choosers = fortune_wheel_obj.pineapple_choosers.all()
            played_diamonds = fortune_wheel_obj.pineapple_played_diamonds
            winning_diamonds = pineapple_total_winning_diamonds

        if len(choosers) > 0:
            # Updating winner database
            played_diamonds = json.loads(played_diamonds)
            json_data = {}
            update_list = []
            for user_obj in choosers:
                invested_diamonds = played_diamonds[f"{user_obj.id}"]
                gain_diamonds = times * invested_diamonds
                profile_obj = user_obj.profile
                profile_obj.diamonds += gain_diamonds
                # profile_obj.received_diamonds += gain_diamonds
                update_list.append(profile_obj)
                json_data[str(user_obj.id)] = gain_diamonds
            if len(update_list) > 0:
                Profile.objects.bulk_update(update_list, ["diamonds"],batch_size=len(update_list))
            fortune_wheel_obj.winning_diamonds = json.dumps(json_data)
            try:
                games_diamonds_obj = GamesDiamonds.objects.first()
                if games_diamonds_obj:
                    games_diamonds_obj.recent_diamonds -= winning_diamonds
                    games_diamonds_obj.save(force_update=True)                    
            except:
                pass

        # Winner item history
        winner_history = fortune_wheel_obj.winner_history
        if winner_history is None:
            fortune_wheel_obj.winner_history = min_item
        else:
            winner_history = f"{min_item},{winner_history}"
            list_winner_items = winner_history.split(",")
            if len(list_winner_items) < 9:
                fortune_wheel_obj.winner_history = winner_history
            else:
                eight_item = list_winner_items[7]
                list_winner_items = list_winner_items[:7]
                winner_history = ""
                for item in list_winner_items:
                    winner_history += f"{item},"
                winner_history += eight_item
                fortune_wheel_obj.winner_history = winner_history
        fortune_wheel_obj.save(force_update=True)
    return 'spinning fortune wheel game result is processing'
