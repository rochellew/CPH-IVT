from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from . import views


app_name = 'priv'
urlpatterns = [
    # home/dashboard
    path('home/<int:indicator>/',
         login_required(views.PrivDashboardView.as_view()),
         name='dashboardselected'),
    path('home/',
         login_required(views.PrivDashboardView.as_view()),
         name='dashboard1'),
    # creating new health indicators
    path('indicator/add/',
         login_required(views.HealthIndicatorCreate.as_view()),
         name='createIndicator'),
    # update an existing health indicator
    path('indicator/update/<int:post_pk>/',
         login_required(views.HealthIndicatorUpdate.as_view()),
         name='updateIndicator'),
    # delete an existing health indicator
    path('indicator/delete/<int:post_pk>/',
         login_required(views.HealthIndicatorDelete.as_view()),
         name='deleteIndicator'),
    # delete an existing dataset
    path('dataset/delete/<int:post_pk>/',
         login_required(views.DataSetDelete.as_view()),
         name='deleteDataset'),
    # upload page
    path('upload/',
         login_required(views.UploadNewDataView.as_view()),
         name='uploadData'),
    # login
    path('login/',
         LoginView.as_view(template_name='hda_privileged/login.html', ),
         name='login'),
    # logout
    path('logout/', views.logout_view, name='logout'),
    # user management: Kim Hawkins
    path('usermanagement',
         login_required(views.user_management.as_view()), name='user_mgmt'),
    path('user/create', login_required(views.CreateNewPrivUser), name='create_user'),
    path('user/password/reset/<int:user>',
         login_required(views.PasswordReset.as_view()), name='pswd_reset'),
    path('user/deactivate/<int:user>',
         login_required(views.DelPrivUser.as_view()), name='deactivate'),
]
