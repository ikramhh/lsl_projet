from rest_framework import serializers
from .models import Translation, History
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'groups']
        read_only_fields = ['id']


class TranslationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Translation
        fields = ['id', 'user', 'username', 'text', 'confidence', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # Automatically set user from request
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)


class HistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = History
        fields = ['id', 'user', 'username', 'translation', 'confidence', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # Automatically set user from request
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)