from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views import View
from .models import Post, UserProfile, Tag, Identifier, UserOTP, Article, AccountType, VerificationRequest, APIAccessLog
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import PostForm, ExploreForm, IdentifierFormSet, IdentifierSearchForm, OTPVerificationForm, ArticleForm, CustomSignupForm, PoliceVerificationForm, SecurityCompanyVerificationForm, InvestigationUpdateForm
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib import messages
from collections import Counter
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
import secrets


def send_otp_email(user):
    otp_obj, created = UserOTP.objects.get_or_create(user=user)
    otp_obj.generate_otp()

    subject = "Your OTP for Account Verification"
    message = f"Hello {user.username},\n\nYour OTP is {otp_obj.otp}"
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email])

def resend_otp_view(request):
    if request.user.is_authenticated and not request.user.profile.is_verified:
        send_otp_email(request.user)
        messages.success(request, "A new OTP has been sent to your email.")
    else:
        messages.warning(request, "You are either already verified or not logged in.")
    return redirect('verify_otp')

def verify_otp_view(request):
    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = form.cleaned_data['otp']
            try:
                user = User.objects.get(email=email)
                otp_obj = UserOTP.objects.get(user=user)
                if otp_obj.otp == otp:
                    user.is_active = True
                    user.save()
                    if hasattr(user, 'profile'):
                        user.profile.is_verified = True
                        user.profile.save()
                    messages.success(request, "Account verified! You can now log in.")
                    return redirect('login')
                else:
                    messages.error(request, "Incorrect OTP.")
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
    else:
        form = OTPVerificationForm()
    return render(request, 'social/verify_otp.html', {'form': form})


class AccountTypeSignupView(View):
    def get(self, request, *args, **kwargs):
        form = CustomSignupForm()
        return render(request, 'account/account_type_signup.html', {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            account_type = form.cleaned_data['account_type']
            
            if account_type == AccountType.CITIZEN:
                send_otp_email(user)
                messages.info(request, "Please check your email for OTP verification.")
                return redirect('verify_otp')
            else:
                messages.info(request, f"Please complete the verification process for {account_type} account.")
                return redirect('submit_verification')
        
        return render(request, 'account/account_type_signup.html', {'form': form})

class SubmitVerificationView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        account_type = request.user.account_type.account_type
        
        if account_type == AccountType.POLICE:
            form = PoliceVerificationForm()
            template = 'social/police_verification.html'
        elif account_type == AccountType.SECURITY_COMPANY:
            form = SecurityCompanyVerificationForm()
            template = 'social/security_verification.html'
        else:
            messages.info(request, "Citizens don't need additional verification.")
            return redirect('post_list')
        
        return render(request, template, {'form': form})
    
    def post(self, request, *args, **kwargs):
        account_type = request.user.account_type.account_type
        
        if account_type == AccountType.POLICE:
            form = PoliceVerificationForm(request.POST, request.FILES)
        elif account_type == AccountType.SECURITY_COMPANY:
            form = SecurityCompanyVerificationForm(request.POST, request.FILES)
        else:
            return redirect('post_list')
        
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.account_type = account_type
            verification.save()
            
            messages.success(request, "Verification request submitted. You'll be notified once approved.")
            return redirect('verification_pending')
        
        if account_type == AccountType.POLICE:
            template = 'social/police_verification.html'
        else:
            template = 'social/security_verification.html'
        
        return render(request, template, {'form': form})
    
class VerificationPendingView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        verification = VerificationRequest.objects.filter(user=request.user).last()
        return render(request, 'social/verification_pending.html', {'verification': verification})
    
class PoliceDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'account_type') and self.request.user.account_type.is_police()
    
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        
        stats = {
            'total_reports': posts.count(),
            'under_investigation': posts.filter(investigation_status='UNDER_INVESTIGATION').count(),
            'investigated': posts.filter(investigation_status='INVESTIGATED').count(),
            'closed': posts.filter(investigation_status='CLOSED').count(),
        }
        
        crime_stats = CrimeType.objects.annotate(
            report_count=Count('post')
        ).order_by('-report_count')
        
        context = {
            'posts': posts,
            'stats': stats,
            'crime_stats': crime_stats,
        }
        
        return render(request, 'social/police_dashboard.html', context)

class UpdateInvestigationView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'account_type') and self.request.user.account_type.is_police()
    
    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = InvestigationUpdateForm(instance=post)
        return render(request, 'social/update_investigation.html', {'form': form, 'post': post})
    
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = InvestigationUpdateForm(request.POST, instance=post)
        
        if form.is_valid():
            investigation = form.save(commit=False)
            investigation.investigating_officer = request.user
            investigation.investigation_updated = timezone.now()
            investigation.save()
            
            messages.success(request, "Investigation status updated successfully.")
            return redirect('police_dashboard')
        
        return render(request, 'social/update_investigation.html', {'form': form, 'post': post})

class SecurityDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'account_type') and self.request.user.account_type.is_security_company()
    
    def get(self, request, *args, **kwargs):
        account = request.user.account_type
        
        posts = Post.objects.all().order_by('-created_on')[:20]
        
        api_stats = {
            'api_key': account.api_key or 'Not generated',
            'calls_used': account.api_calls_used,
            'calls_limit': account.api_calls_limit,
            'subscription_tier': account.subscription_tier or 'None',
            'subscription_expiry': account.subscription_expiry,
        }
        
        context = {
            'posts': posts,
            'api_stats': api_stats,
            'account': account,
        }
        
        return render(request, 'social/security_dashboard.html', context)

@login_required
def generate_api_key(request):
    if not (hasattr(request.user, 'account_type') and request.user.account_type.is_security_company()):
        return HttpResponseForbidden("Only security companies can generate API keys.")
    
    account = request.user.account_type
    account.api_key = secrets.token_urlsafe(32)
    account.save()
    
    messages.success(request, "New API key generated successfully.")
    return redirect('security_dashboard')

class CrimeDataAPIView(View):
    def get(self, request, *args, **kwargs):
        api_key = request.GET.get('api_key')
        
        if not api_key:
            return JsonResponse({'error': 'API key required'}, status=401)
        
        try:
            account = AccountType.objects.get(api_key=api_key)
            if not account.is_security_company():
                return JsonResponse({'error': 'Invalid API key'}, status=401)
            
            if account.api_calls_used >= account.api_calls_limit:
                return JsonResponse({'error': 'API limit exceeded'}, status=429)
            
            APIAccessLog.objects.create(
                user=account.user,
                endpoint='/api/crime-data',
                ip_address=request.META.get('REMOTE_ADDR', ''),
                response_code=200
            )
            
            account.api_calls_used += 1
            account.save()
            
            posts = Post.objects.all().order_by('-created_on')[:10]
            data = []
            for post in posts:
                data.append({
                    'id': post.id,
                    'crime_types': [ct.name for ct in post.crime_types.all()],
                    'location': f"{post.location_city}, {post.location_province}",
                    'date': post.incident_date.isoformat(),
                    'status': post.investigation_status,
                })
            
            return JsonResponse({'data': data, 'calls_remaining': account.api_calls_limit - account.api_calls_used})
            
        except AccountType.DoesNotExist:
            return JsonResponse({'error': 'Invalid API key'}, status=401)

class PostListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        form = PostForm()
        identifier_formset = IdentifierFormSet()

        identifier_counts = {}
        for identifier in Identifier.objects.all():
            identifier_counts[identifier.value] = identifier_counts.get(identifier.value, 0) + 1

        context = {
            'post_list': posts,
            'form': form,
            'identifier_formset': identifier_formset,
            'identifier_counts' : identifier_counts,
        }
        return render(request, 'social/post_list.html', context)

    def post(self, request, *args, **kwargs):

        form = PostForm(request.POST, request.FILES)
        identifier_formset = IdentifierFormSet(request.POST)
        posts = Post.objects.all().order_by('-created_on')

        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            form.save_m2m()
            new_post.create_tags()

            for identifier_form in identifier_formset:
                if identifier_form.cleaned_data and not identifier_form.cleaned_data.get('DELETE', False):
                    Identifier.objects.create(
                        post=new_post,
                        identifier_type=identifier_form.cleaned_data['identifier_type'],
                        value=identifier_form.cleaned_data['value']
                    )

            return redirect('post_list')

        context = {
            'post_list': posts,
            'form': form,
            'identifier_formset': identifier_formset,
        }

        return render(request, 'social/post_list.html', context)


class PostDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        
        can_view_evidence = False
        if hasattr(request.user, 'account_type'):
            can_view_evidence = request.user.account_type.can_view_evidence()

        identifiers = post.identifiers.values_list('value', flat=True)

        related_posts = Post.objects.filter(
            identifiers__value__in=identifiers
        ).exclude(id=post.id).distinct()

        all_identifiers = Identifier.objects.values_list('value', flat=True)
        identifier_counts = Counter(all_identifiers)

        context = {
            'post': post,
            'related_posts': related_posts,
            'identifier_counts': identifier_counts,
            'can_view_evidence': can_view_evidence,
        }
        return render(request, 'social/post_detail.html', context)


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['body']
    template_name =  'social/post_edit.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('post_detail', kwargs={'pk': pk})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'social/post_delete.html'
    success_url = reverse_lazy('post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class ProfileView(View):
    def get(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk=pk)
        user = profile.user
        posts = Post.objects.filter(author=user).order_by('-created_on')

        context = {
            'user': user,
            'profile': profile,
            'posts': posts
        }
        return render(request, 'social/profile.html', context)

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    fields = ['name', 'bio', 'birth_date', 'location', 'picture']
    template_name = 'social/profile_edit.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('profile', kwargs={'pk': pk})

    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user


class UserSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get('query')
        profile_list = UserProfile.objects.filter(
            Q(user__username__icontains=query)
        )
        context = {
            'profile_list': profile_list,
        }

        return render(request, 'social/search.html', context)

class IdentifierSearchView(View):
    def get(self, request, *args, **kwargs):
        form = IdentifierSearchForm(request.GET or None)
        results = []

        if form.is_valid():
            query = form.cleaned_data['query']
            matches = Identifier.objects.filter(value__iexact=query)
            results = Post.objects.filter(identifiers__in=matches).distinct()

        context = {
            'form': form,
            'results': results,
            'query': request.GET.get('query', '')
        }
        return render(request, 'social/identifier_search.html', context)


class Explore(View):
    def get(self, request, *args, **kwargs):
        explore_form = ExploreForm()
        query = self.request.GET.get('query')
        tag = Tag.objects.filter(name=query).first()

        if tag:
            posts = Post.objects.filter(tags__in=[tag])
        else:
            posts = Post.objects.all()

        context = {
            'tag': tag,
            'posts':posts,
            'explore_form': explore_form,
        }
        return render(request, 'social/explore.html', context)

    def post(self, request, *args, **kwargs):
        explore_form = ExploreForm(request.POST)
        if explore_form.is_valid():
            query = explore_form.cleaned_data['query']
            tag = Tag.objects.filter(name=query).first()

            posts = None
            if tag:
                posts = Post.objects.filter(tags__in=[tag])

            if posts:
                context = {
                    'tag': tag,
                    'posts' : posts,
                }
            else:
                context = {
                    'tag' : tag,
                }
            return  HttpResponseRedirect(f'/social/explore?query={query}')
        return HttpResponseRedirect('/social/explore')

class ArticleDetailView(View):
    def get(self, request, pk, *args, **kwargs):
        article = Article.objects.get(pk=pk)
        return render(request, 'social/article_detail.html', {'article': article})

class CrimeArticleView(View):
    def get(self, request, *args, **kwargs):
        category = request.GET.get('category')
        search_query = request.GET.get('search')

        articles = Article.objects.all()

        if category:
            articles = articles.filter(category__iexact=category)

        if search_query:
            articles = articles.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )

        articles = articles.order_by('-created_on')
        categories = Article.objects.values_list('category', flat=True).distinct()

        return render(request, 'social/crime_article.html', {
            'articles': articles,
            'categories': categories,
            'selected_category': category,
            'search_query': search_query
        })

class AddArticleView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        form = ArticleForm()
        return render(request, 'social/add_article.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('crime_article')
        return render(request, 'social/add_article.html', {'form': form})

class DonationPageView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'social/donate.html')