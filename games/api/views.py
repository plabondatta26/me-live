from datetime import timedelta
import json
from django.utils import timezone
from django.conf import settings
from games.api.constants import FORTUNE_WHEEL

from games.models import FortuneWheel
from me_live.utils.utils import DateTimeEncoder
from rest_framework.generics import (
    CreateAPIView, UpdateAPIView,
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    HTTP_200_OK,
    )
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from tracking.models import GamesDiamonds

class FortuneWheelItemSelectionCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data_obj = request.data
        user_obj = request.user
        user_id = user_obj.id
        profile_obj = user_obj.profile

        full_name = profile_obj.full_name
        photo_url = get_profile_image(obj=profile_obj)
        item_name = data_obj.get('item_name',None)
        diamonds = data_obj.get('diamonds',0)

        
        if item_name is not None and diamonds > 0:
            if profile_obj.diamonds < diamonds:
                return Response(status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            fortune_wheel_obj = FortuneWheel.objects.first()
            if item_name == 'mango':
                fortune_wheel_obj.mango += diamonds
                fortune_wheel_obj.mango_choosers.add(user_obj)
                json_data = json.loads(fortune_wheel_obj.mango_played_diamonds)
                try:
                    json_data[str(user_id)] += diamonds
                except:
                    json_data[str(user_id)] = diamonds
                fortune_wheel_obj.mango_played_diamonds = json.dumps(json_data)
            elif item_name == 'strawberry':
                fortune_wheel_obj.strawberry += diamonds
                fortune_wheel_obj.strawberry_choosers.add(user_obj)
                json_data = json.loads(fortune_wheel_obj.strawberry_played_diamonds)
                try:
                    json_data[str(user_id)] += diamonds
                except:
                    json_data[str(user_id)] = diamonds
                fortune_wheel_obj.strawberry_played_diamonds = json.dumps(json_data)

            elif item_name == 'coconut':
                fortune_wheel_obj.coconut += diamonds
                fortune_wheel_obj.coconut_choosers.add(user_obj)
                json_data = json.loads(fortune_wheel_obj.coconut_played_diamonds)
                try:
                    json_data[str(user_id)] += diamonds
                except:
                    json_data[str(user_id)] = diamonds
                fortune_wheel_obj.coconut_played_diamonds = json.dumps(json_data)

            elif item_name == 'apple':
                fortune_wheel_obj.apple += diamonds
                fortune_wheel_obj.apple_choosers.add(user_obj)
                json_data = json.loads(fortune_wheel_obj.apple_played_diamonds)
                try:
                    json_data[str(user_id)] += diamonds
                except:
                    json_data[str(user_id)] = diamonds
                fortune_wheel_obj.apple_played_diamonds = json.dumps(json_data)

            elif item_name == 'cucumber':
                fortune_wheel_obj.cucumber += diamonds
                fortune_wheel_obj.cucumber_choosers.add(user_obj)
                json_data = json.loads(fortune_wheel_obj.cucumber_played_diamonds)
                try:
                    json_data[str(user_id)] += diamonds
                except:
                    json_data[str(user_id)] = diamonds
                fortune_wheel_obj.cucumber_played_diamonds = json.dumps(json_data)

            elif item_name == 'pineapple':
                fortune_wheel_obj.pineapple += diamonds
                fortune_wheel_obj.pineapple_choosers.add(user_obj)
                json_data = json.loads(fortune_wheel_obj.pineapple_played_diamonds)
                try:
                    json_data[str(user_id)] += diamonds
                except:
                    json_data[str(user_id)] = diamonds
                fortune_wheel_obj.pineapple_played_diamonds = json.dumps(json_data)


            played_diamonds = json.loads(fortune_wheel_obj.played_diamonds)
            played_diamonds.append({"uid":user_id,"diamonds": diamonds,"datetime":(timezone.now() + timedelta(seconds=1))})
            fortune_wheel_obj.played_diamonds = DateTimeEncoder().encode(played_diamonds)
            fortune_wheel_obj.players.add(user_obj) 

            top_played_diamonds = json.loads(fortune_wheel_obj.top_played_diamonds)
            if len(top_played_diamonds) == 0:
                top_played_diamonds.append({"uid":user_id,"full_name":full_name,"profile_image":photo_url,"diamonds": diamonds,})
            else:
                # top_played_diamonds = [num for num in top_played_diamonds if num["uid"] == user_id]
                exists = False
                for played_diamond in top_played_diamonds:
                    if played_diamond["uid"] == user_id:
                        my_diamonds = played_diamond["diamonds"]
                        played_diamond["diamonds"] = my_diamonds + diamonds
                        exists = True
                        break

                if exists == False:
                    top_played_diamonds.append({"uid":user_id,"full_name":full_name,"profile_image":photo_url,"diamonds": diamonds,})
                        
            fortune_wheel_obj.top_played_diamonds = json.dumps(top_played_diamonds)
            fortune_wheel_obj.save(force_update=True)

            profile_obj.diamonds -= diamonds
            # profile_obj.sent_diamonds += diamonds
            profile_obj.save(force_update=True)
            try:
                games_diamonds_obj = GamesDiamonds.objects.first()
                if games_diamonds_obj:
                    games_diamonds_obj.recent_diamonds += diamonds
                    games_diamonds_obj.save(force_update=True)
            except:
                pass

            return Response(status=HTTP_201_CREATED)

        return Response(status=HTTP_204_NO_CONTENT)

class GameViewersUpdateApiView(UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        data_obj = request.data
        user_obj = request.user

        game_type = data_obj.get('game_type',None)
        is_viewing = data_obj.get('is_viewing',False)

        if game_type == FORTUNE_WHEEL:
            fortune_wheel_obj = FortuneWheel.objects.first()
            if fortune_wheel_obj:
                if is_viewing == True:
                    fortune_wheel_obj.viewers.add(user_obj)
                else:
                    fortune_wheel_obj.viewers.remove(user_obj)
        return Response(status=HTTP_200_OK) 

def get_profile_image(obj):
        if obj.profile_image:
            return f"{settings.BASE_URL}/media/{obj.profile_image}"
        return obj.photo_url