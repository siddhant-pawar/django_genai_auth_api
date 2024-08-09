from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from .utils import summarize_text, generate_image_from_text,extract_text_from_file
from .textvid import generate_text, create_video_clip, create_final_video, setup_folders,generate_image_description
from rest_framework import status
from .models import UserProfile, Document, ProcessedData, SubscriptionPlan, UserSubscription
from .serializers import (
                        TextSerializer,
                        TextvidPromptSerializer,
                        PromptSerializer, 
                        FileSerializer, 
                        UserSerializer, 
                        UserProfileSerializer, 
                        DocumentSerializer,
                        ProcessedDataSerializer, 
                        SubscriptionPlanSerializer, 
                        UserSubscriptionSerializer)
import logging
from django.db import transaction

logger = logging.getLogger(__name__)
User = get_user_model()

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tabs'] = [
            {'id': 'SummarizeText', 'title': 'Summarize Text'},
            {'id': 'GenerateImage', 'title': 'Generate Image'},
            {'id': 'GenerateTextandVideo', 'title': 'Generate Text and Video'},
            {'id': 'UploadFile', 'title': 'Upload File'}
        ]
        return context

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    #permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def get_all_users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class SummarizeTextView(APIView):
    def post(self, request):
        serializer = TextSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        text = serializer.validated_data['text']
        try:
            summary = summarize_text(text)
            if summary:
                return Response({'summary-result': summary}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to generate summary.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error in SummarizeTextView: {str(e)}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateImageView(APIView):
    def post(self, request):
        serializer = PromptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        prompt = serializer.validated_data['prompt']
        try:
            image_url = generate_image_from_text(prompt)
            if image_url:
                return Response({'image_url': image_url}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to generate image.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error in GenerateImageView: {str(e)}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#i learned cicd pipeline 
class GenerateTextView(APIView):
    def post(self, request):
        logger.info("Received POST request with data: %s", request.data)
        serializer = TextvidPromptSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error("Serializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        textprompt = serializer.validated_data['textprompt']
        
        try:
            # Perform all operations within a transaction
            with transaction.atomic():
                # Cleanup and setup folders
                self.setup_folders()

                # Generate text based on the prompt
                generated_text = self.generate_text_with_logging(textprompt)
                if not generated_text:
                    return Response({"error": "Failed to generate text."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Split the generated text into paragraphs
                paragraphs = generated_text.split('\n\n')

                # Generate video clips for each paragraph
                for index, para in enumerate(paragraphs):
                    video_path, error = self.create_video_clip_with_logging(para, index)
                    if error:
                        return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Create the final video by concatenating all video clips
                final_video_path = self.create_final_video_with_logging()
            
            return Response({
                "final_video_path": f"/{final_video_path}",
                "generated_text": generated_text
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("An error occurred during video generation")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def setup_folders(self):
        try:
            setup_folders()
        except Exception as e:
            logger.error("Error setting up folders: %s", str(e))
            raise

    def generate_text_with_logging(self, textprompt):
        generated_text = generate_text(textprompt)
        if not generated_text:
            logger.error("Failed to generate text for prompt: %s", textprompt)
        return generated_text

    def create_video_clip_with_logging(self, para, index):
        try:
            video_path, error = create_video_clip(para, index)
            if error:
                logger.error("Error generating video clip for paragraph %d: %s", index, error)
            return video_path, error
        except Exception as e:
            logger.error("Exception during video clip creation for paragraph %d: %s", index, str(e))
            raise

    def create_final_video_with_logging(self):
        try:
            final_video_path = create_final_video()
            logger.info("Successfully generated final video: %s", final_video_path)
            return final_video_path
        except Exception as e:
            logger.error("Exception during final video creation: %s", str(e))
            raise

        
class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = FileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        try:
            text = extract_text_from_file(file)
            if text:
                summary = summarize_text(text)
                return Response({'text': text, 'summary': summary}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to extract text from file.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error in FileUploadView: {str(e)}")
            return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class ProcessedDataViewSet(viewsets.ModelViewSet):
    queryset = ProcessedData.objects.all()
    serializer_class = ProcessedDataSerializer


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
