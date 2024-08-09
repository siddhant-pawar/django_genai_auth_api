from django.urls import path, include
from rest_framework import routers
from .views import ( 
                    HomeView,
                    FileUploadView, 
                    GenerateTextView,
                    SummarizeTextView,
                    GenerateImageView,
                    UserViewSet,
                    UserProfileViewSet,
                    DocumentViewSet,
                    ProcessedDataViewSet,
                    SubscriptionPlanViewSet,
                    UserSubscriptionViewSet)

router = routers.DefaultRouter()
router.register('users', UserViewSet)
router.register('user-profiles', UserProfileViewSet)
router.register('documents', DocumentViewSet)
router.register('processed-data', ProcessedDataViewSet)
router.register('subscription-plans', SubscriptionPlanViewSet)
router.register('user-subscriptions', UserSubscriptionViewSet)

urlpatterns = [
    path('basedapi/', include(router.urls)),
    path('', HomeView.as_view(), name='home'),
    path('summarize-text/', SummarizeTextView.as_view(), name='summary-result'),
    path('generate-image/', GenerateImageView.as_view(), name='generate_image'),
    path('upload-file/', FileUploadView.as_view(), name='upload_file'),
    path('generate-text/', GenerateTextView.as_view(), name='generate_text'),

]
