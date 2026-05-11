import json
from django.utils import timezone
from dateutil import parser
from re import search
from rest_framework import serializers
from games.models import (
    FortuneWheel, 
    )

class FortuneWheelSerializer(serializers.ModelSerializer):
    winner_history = serializers.SerializerMethodField()
    played_diamonds = serializers.SerializerMethodField()
    top_played_diamonds = serializers.SerializerMethodField()

    class Meta:
        model = FortuneWheel
        fields = ['id','mango','mango_times','mango_choosers','mango_played_diamonds','strawberry','strawberry_times','strawberry_choosers','strawberry_played_diamonds',
        'coconut','coconut_times','coconut_choosers','coconut_played_diamonds','apple','apple_times','apple_choosers','apple_played_diamonds',
        'cucumber','cucumber_times','cucumber_choosers','cucumber_played_diamonds','pineapple','pineapple_times','pineapple_choosers','pineapple_played_diamonds',
        'viewers','players','played_diamonds','top_played_diamonds', 
        'winner_index','winning_diamonds','winner_history','updated_datetime',
        ]

    def get_winner_history(self,obj):
        if obj.winner_history is None:
            return [] 
        elif search(",",obj.winner_history):
            return obj.winner_history.split(",")
        else:
            return [obj.winner_history]

    def get_played_diamonds(self,obj):
        played_diamonds = json.loads(obj.played_diamonds)
        played_diamonds = [num for num in played_diamonds if parser.parse(num['datetime']) >= timezone.now()]
        return played_diamonds

    def get_top_played_diamonds(self,obj):
        top_played_diamonds = json.loads(obj.top_played_diamonds)
        if len(top_played_diamonds) > 1:
            top_played_diamonds.sort(key=lambda x: x['diamonds'], reverse=True)
        return top_played_diamonds
