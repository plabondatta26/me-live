import json
from celery import shared_task
from django.core.cache import cache
from profiles.models import Profile
from balance.models import (
    Contribution,
    )
from profiles.api.serializers import ProfileSerializer

@shared_task
def process_top_contributor_ranking():
    
    top20_contributors = getTopContributorList(list_range=20,)
    # Home page Top Contributors
    cache.set("top_contributors",top20_contributors,timeout=60*60)
    # Home page Slider
    cache.set("top_sliding_contributors",top20_contributors[:5],timeout=60*60)
            
    return 'process_top_contributor_ranking is processing'
    
def contributionFunc(e):
  return e['diamonds']
    
def getTopContributorList(list_range):
    top_contributors = []
    contribution_objs = Contribution.objects.all().select_related('contributor')
    if contribution_objs:

        tracking_array = []
        json_data = {}
        for contribution_obj in contribution_objs:
            try:
                json_data[f"{contribution_obj.contributor.id}"] = json_data[f"{contribution_obj.contributor.id}"] + contribution_obj.diamonds
            except:
                json_data[f"{contribution_obj.contributor.id}"] = contribution_obj.diamonds

        str_json_data = json.dumps(json_data)

        str_json_data = str_json_data.split("{")[1].split("}")[0]

        str_array = str_json_data.split(",")

        for str_item in str_array:
            inner_item_array = str_item.split(":")

            str_item = inner_item_array[0].strip().split("\"")[1].split("\"")[0]
            data = {
                "uid": int(str_item),
                "diamonds": int(inner_item_array[1]),
            }
            tracking_array.append(data)

        tracking_array.sort(reverse=True,key=contributionFunc)

        top_list = tracking_array[:list_range]

        for top_item in top_list:
            profile_cache = cache.get(f'profile_{top_item["uid"]}')
            if profile_cache is None:
                profile_obj = Profile.objects.filter(user__id=top_item["uid"]).first()
                if profile_obj:
                    # serializer_profile = ProfileForUserInfoSerializer(instance=profile_obj)
                    serializer_profile = ProfileSerializer(instance=profile_obj,)
                    profile_cache = serializer_profile.data
                    cache.set(f'profile_{top_item["uid"]}',profile_cache,timeout=60*60*24*2)

            try:
                profile_cache['vvip_or_vip_preference'] = json.loads(profile_cache['vvip_or_vip_preference'])
            except:
                pass


            data = {
                "uid": top_item["uid"],
                "level": profile_cache["level"],
                "vvip_or_vip_preference": profile_cache["vvip_or_vip_preference"],
                "full_name": profile_cache["full_name"],
                "profile_image": profile_cache["profile_image"],
                "diamonds": top_item["diamonds"],
                "is_agent": profile_cache["is_agent"],
                "is_reseller": profile_cache["is_reseller"],
                "is_host": profile_cache["is_host"],
                "is_moderator": profile_cache["is_moderator"],
            }

            top_contributors.append(data)
    return top_contributors
