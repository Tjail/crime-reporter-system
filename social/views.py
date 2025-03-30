from django.shortcuts import render, redirect
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views import View
from .models import Post, UserProfile, Tag, Identifier, UserOTP, Article
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import PostForm, ExploreForm, IdentifierFormSet, IdentifierSearchForm, OTPVerificationForm, ArticleForm
from django.views.generic.edit import UpdateView, DeleteView
from django.contrib import messages
from collections import Counter
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


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
                    messages.success(request, "Account verified! You can now log in.")
                    return redirect('login')
                else:
                    messages.error(request, "Incorrect OTP.")
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
    else:
        form = OTPVerificationForm()
    return render(request, 'social/verify_otp.html', {'form': form})

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

        # Get identifier values from this post
        identifiers = post.identifiers.values_list('value', flat=True)

        #Find related posts
        related_posts = Post.objects.filter(
            identifiers__value__in=identifiers
        ).exclude(id=post.id).distinct()

        all_identifiers = Identifier.objects.values_list('value', flat=True)
        identifier_counts = Counter(all_identifiers)

        context = {
            'post': post,
            'related_posts': related_posts,
            'identifier_counts': identifier_counts
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