from django.core.cache import cache
from rest_framework.generics import (
    RetrieveAPIView,
    )
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey
from rest_framework.status import (
    HTTP_200_OK,
    )
from ..models import AppLock

class AppLockRetrieveApiView(RetrieveAPIView):
    authentication_classes = []
    permission_classes = [HasAPIKey]
 
    def retrieve(self, request, *args, **kwargs):
        build_number = cache.get('build_number')
        if build_number is None:
            applocK_obj = AppLock.objects.first()
            if applocK_obj:
                build_number = applocK_obj.build_number
                cache.set('build_number',build_number,timeout=60*60*24*7)
            else:
                build_number = 0
            
        return Response({"build_number": build_number},status=HTTP_200_OK)
