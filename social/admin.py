#this file is social/admin.py
from django.contrib import admin
from .models import (CrimeType, Post, Identifier, UserProfile, Tag, Article, 
                     AccountType, VerificationRequest, APIAccessLog, User)
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from django.urls import path
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.sites.admin import SiteAdmin
from allauth.account.admin import EmailAddressAdmin
from allauth.socialaccount.admin import SocialAccountAdmin, SocialAppAdmin, SocialTokenAdmin
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken

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
    
class CrimeWatchAdminSite(AdminSite):
    site_header = 'CrimeWatch Reporting System Administration'
    site_title = 'CrimeWatch Reporting System Admin'
    index_title = 'CrimeWatch Reporting System Administration Panel'
    
    def index(self, request, extra_context=None):
        return admin_index_view(request, extra_context)
    
@staff_member_required
def admin_dashboard(request):
    stats = {
        'pending_verifications': VerificationRequest.objects.filter(status='PENDING').count(),
        'total_reports': Post.objects.count(),
        'total_users': User.objects.count(),
        'verified_police': AccountType.objects.filter(account_type='POLICE', is_verified=True).count(),
        'verified_security': AccountType.objects.filter(account_type='SECURITY', is_verified=True).count(),
    }
    
    recent_verifications = VerificationRequest.objects.order_by('-submitted_at')[:5]
    recent_reports = Post.objects.order_by('-created_on')[:5]
    
    crime_stats = CrimeType.objects.annotate(
        report_count=Count('post')
    ).order_by('-report_count')[:5]
    
    context = {
        'stats': stats,
        'recent_verifications': recent_verifications,
        'recent_reports': recent_reports,
        'crime_stats': crime_stats,
    }
    
    return render(request, 'admin/custom_dashboard.html', context)

@staff_member_required
def verification_management(request):
    status_filter = request.GET.get('status', 'PENDING')
    account_filter = request.GET.get('account_type', '')
    
    verifications = VerificationRequest.objects.all().order_by('-submitted_at')
    
    if status_filter:
        verifications = verifications.filter(status=status_filter)
    if account_filter:
        verifications = verifications.filter(account_type=account_filter)
    
    paginator = Paginator(verifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'account_filter': account_filter,
        'status_choices': VerificationRequest.STATUS_CHOICES,
        'account_choices': AccountType.ACCOUNT_TYPE_CHOICES,
    }
    
    return render(request, 'admin/verification_management.html', context)

@staff_member_required
def verification_detail(request, pk):
    verification = get_object_or_404(VerificationRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            verification.status = 'APPROVED'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.save()
            
            account = verification.user.account_type
            account.is_verified = True
            account.verification_date = timezone.now()
            account.verified_by = request.user
            
            if verification.account_type == AccountType.POLICE:
                account.badge_number = verification.police_badge_number
                account.station = verification.police_station
                account.rank = verification.police_rank
            elif verification.account_type == AccountType.SECURITY_COMPANY:
                account.company_name = verification.company_name
                account.company_registration = verification.company_registration
                account.psira_number = verification.psira_number
                account.subscription_tier = 'BASIC'
            
            account.save()
            messages.success(request, f"Verification approved for {verification.user.username}")
            
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            verification.status = 'REJECTED'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.rejection_reason = rejection_reason
            verification.save()
            
            messages.success(request, f"Verification rejected for {verification.user.username}")
        
        return redirect('admin_verification_management')
    
    return render(request, 'admin/verification_detail.html', {'verification': verification})

@staff_member_required
def reports_management(request):
    reports = Post.objects.all().order_by('-created_on')
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(investigation_status=status_filter)
    
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Post.INVESTIGATION_STATUS,
    }
    
    return render(request, 'admin/reports_management.html', context)

@staff_member_required
def users_management(request):
    users = User.objects.select_related('account_type').order_by('-date_joined')
    
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) | 
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    
    return render(request, 'admin/users_management.html', context)

def admin_index_view(request, extra_context=None):
    """
    Custom admin index view with statistics
    """
    stats = {
        'pending_verifications_count': VerificationRequest.objects.filter(status='PENDING').count(),
        'total_reports_count': Post.objects.count(),
        'total_users_count': User.objects.count(),
        'verified_police_count': AccountType.objects.filter(account_type='POLICE', is_verified=True).count(),
        'verified_security_count': AccountType.objects.filter(account_type='SECURITY', is_verified=True).count(),
    }
    
    context = {
        'title': 'Administration',
        **stats,
        **(extra_context or {})
    }
    
    app_list = admin.site.get_app_list(request)
    context['app_list'] = app_list
    
    return TemplateResponse(request, 'admin/index.html', context)

admin_site = CrimeWatchAdminSite(name='admin')

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)

admin_site.register(Site, SiteAdmin)

admin_site.register(EmailAddress, EmailAddressAdmin)
admin_site.register(SocialAccount, SocialAccountAdmin)
admin_site.register(SocialApp, SocialAppAdmin)
admin_site.register(SocialToken, SocialTokenAdmin)

admin_site.register(CrimeType)
admin_site.register(Identifier)
admin_site.register(UserProfile)
admin_site.register(Tag)
admin_site.register(Article)
admin_site.register(AccountType, AccountTypeAdmin)
admin_site.register(VerificationRequest, VerificationRequestAdmin)
admin_site.register(Post, PostAdmin)
admin_site.register(APIAccessLog, APIAccessLogAdmin)