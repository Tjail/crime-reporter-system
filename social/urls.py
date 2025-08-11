from django.urls import path, include
from .views import (PostListView, PostDetailView, PostEditView, PostDeleteView, ProfileView, ProfileEditView,
                    UserSearch, Explore, IdentifierSearchView, verify_otp_view, resend_otp_view, AddArticleView,
                    ArticleDetailView, DonationPageView, CrimeArticleView, AccountTypeSignupView, SubmitVerificationView,
                    VerificationPendingView, PoliceDashboardView, SecurityDashboardView,
                    UpdateInvestigationView, CrimeDataAPIView, generate_api_key)
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
    
    path('signup/', AccountTypeSignupView.as_view(), name='account_type_signup'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('submit-verification/', SubmitVerificationView.as_view(), name='submit_verification'),
    path('verification-pending/', VerificationPendingView.as_view(), name='verification_pending'),
    
    path('police/dashboard/', PoliceDashboardView.as_view(), name='police_dashboard'),
    path('police/investigate/<int:pk>/', UpdateInvestigationView.as_view(), name='update_investigation'),
    path('security/dashboard/', SecurityDashboardView.as_view(), name='security_dashboard'),
    path('security/generate-api-key/', generate_api_key, name='generate_api_key'),
    path('api/crime-data/', CrimeDataAPIView.as_view(), name='crime_data_api'),
    
    path('crime-article/', CrimeArticleView.as_view(), name='crime_article'),
    path('crime-article/add/', AddArticleView.as_view(), name='add_article'),
    path('crime-article/<int:pk>/', ArticleDetailView.as_view(), name='article_detail'),
    path('donate/', DonationPageView.as_view(), name='donate'),
    path('map/', include('crime_map.urls')),
]



