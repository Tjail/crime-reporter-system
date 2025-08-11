from django.contrib import admin
from .models import (CrimeType, Post, Identifier, UserProfile, Tag, Article, 
                     AccountType, VerificationRequest, APIAccessLog)
from django.utils import timezone

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_type', 'is_verified', 'verification_date']
    list_filter = ['account_type', 'is_verified']
    search_fields = ['user__username', 'company_name', 'badge_number']
    actions = ['verify_accounts']
    
    def verify_accounts(self, request, queryset):
        queryset.update(is_verified=True, verification_date=timezone.now(), verified_by=request.user)
    verify_accounts.short_description = "Verify selected accounts"

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_type', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['status', 'account_type']
    search_fields = ['user__username']
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        for req in queryset:
            req.status = 'APPROVED'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            
            account = req.user.account_type
            account.is_verified = True
            account.verification_date = timezone.now()
            account.verified_by = request.user
            
            if req.account_type == AccountType.POLICE:
                account.badge_number = req.police_badge_number
                account.station = req.police_station
                account.rank = req.police_rank
            elif req.account_type == AccountType.SECURITY_COMPANY:
                account.company_name = req.company_name
                account.company_registration = req.company_registration
                account.psira_number = req.psira_number
                account.subscription_tier = 'BASIC'
            
            account.save()
    
    def reject_requests(self, request, queryset):
        queryset.update(status='REJECTED', reviewed_by=request.user, reviewed_at=timezone.now())

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'created_on', 'investigation_status', 'investigating_officer']
    list_filter = ['investigation_status', 'created_on']
    search_fields = ['description', 'case_number']

@admin.register(APIAccessLog)
class APIAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint', 'timestamp', 'response_code']
    list_filter = ['response_code', 'timestamp']
    search_fields = ['user__username']

admin.site.register(CrimeType)
admin.site.register(Identifier)
admin.site.register(UserProfile)
admin.site.register(Tag)
admin.site.register(Article)
