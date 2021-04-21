from rest_framework import serializers


class CustomTokenSerializer(serializers.Serializer):
    token = serializers.CharField()