from django.contrib import admin
from .models import UserProfile, Document, ProcessedData, SubscriptionPlan, UserSubscription

class DocumentInline(admin.StackedInline):
    model = Document
    extra = 1

class UserSubscriptionInline(admin.StackedInline):
    model = UserSubscription
    extra = 1

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    inlines = [DocumentInline, UserSubscriptionInline]

@admin.register(ProcessedData)
class ProcessedDataAdmin(admin.ModelAdmin):
    list_display = ('document', 'summary', 'analysis', 'processed_at')
    search_fields = ('document__title', 'summary', 'analysis')
    list_filter = ('processed_at',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'duration_days')
    search_fields = ('name', 'description')
    list_filter = ('duration_days',)

admin.site.register(UserSubscription)
