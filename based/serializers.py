from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from rest_framework import serializers
from .models import UserProfile, Document, ProcessedData, SubscriptionPlan, UserSubscription
from authapi.models import User

class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'name', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'is_admin', 'created_at', 'updated_at']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

class ProcessedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedData
        fields = '__all__'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'


class TextSerializer(serializers.Serializer):
    text = serializers.CharField(
        required=True,
        max_length=5000,  # Adjust the max_length as per your requirements
        error_messages={
            'required': 'Text field is required.',
            'max_length': 'Text exceeds maximum length allowed.'
        }
    )

class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        required=True,
        max_length=500,  # Adjust the max_length as per your requirements
        error_messages={
            'required': 'Prompt field is required.',
            'max_length': 'Prompt exceeds maximum length allowed.'
        }
    )
   
class TextvidPromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(
        required=True,
        max_length=500,  # Adjust the max_length as per your requirements
        error_messages={
            'required': 'Prompt field is required.',
            'max_length': 'Prompt exceeds maximum length allowed.'
        }
    )
    
class FileSerializer(serializers.Serializer):
    file = serializers.FileField(
        required=True,
        error_messages={
            'required': 'File is required.',
            'invalid': 'Invalid file type.'
        }
    )

    def validate_file(self, value):
        # Example of file validation
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']  # Add allowed MIME types
        max_file_size = 5 * 1024 * 1024  # 5 MB limit

        if value.size > max_file_size:
            raise serializers.ValidationError('File size exceeds the maximum limit of 5MB.')
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('File type not supported.')

        return value
