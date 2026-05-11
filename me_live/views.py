from pathlib import Path
import json
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def app_ads(request):
    txt = 'google.com, pub-1671386622468207, DIRECT, f08c47fec0942fa0'
    return HttpResponse(txt, content_type="text/plain")

def deeplink_json_view(request):
    BASE_DIR = Path(__file__).resolve().parent.parent

    path = Path.joinpath(BASE_DIR, "me_live/assetlinks.json")
    json_data = open(path)   
    data = json.load(json_data) # deserialises it
    json_data.close()
  
    return JsonResponse(data,safe=False)