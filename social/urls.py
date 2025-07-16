from django.urls import path, include
from .views import PostListView, PostDetailView, PostEditView, PostDeleteView, ProfileView, ProfileEditView, UserSearch, Explore, IdentifierSearchView, verify_otp_view, resend_otp_view, AddArticleView, ArticleDetailView, DonationPageView
from . import views

urlpatterns = [
    path('', PostListView.as_view(), name='post_list'),
    path('explore/', Explore.as_view(), name='explore'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post_detail'),
    path('post/edit/<int:pk>' , PostEditView.as_view(), name='post_edit'),
    path('post/delete/<int:pk>', PostDeleteView.as_view(), name='post_delete'),
    path('profile/<int:pk>', ProfileView.as_view(), name='profile'),
    path('profile/edit/<int:pk>', ProfileEditView.as_view(), name='profile_edit'),
    path('search/', UserSearch.as_view(), name='profile_search'),
    path('identifier/search/', IdentifierSearchView.as_view(), name='identifier_search'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('crime-article/', views.CrimeArticleView.as_view(), name='crime_article'),
    path('crime-article/add/', AddArticleView.as_view(), name='add_article'),
    path('crime-article/<int:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('donate/', DonationPageView.as_view(), name='donate'),
    path('map/', include('crime_map.urls')),
]



