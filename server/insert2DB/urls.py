from django.urls import path, include
from . import views
from django.views.generic.base import TemplateView
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Path for uploading data
    path('upload/', views.uploadFile, name='uploadFile'),

    # Path for training
    path('train/', views.trainModel, name='trainModel'),

    # Path for creating a user
    url('createUser', views.createUser, name='createUser'),

    # Path for giving permission
    path('permission/', views.givePerm, name='givePerm'),

    # Path for getting all permissions
    path('getpermission/', views.getPerm, name='getPerm'),

    # Path for getting all academic labels
    path('getAcademicLabel/<str:getStudentType>/<str:getYearTerm>/',
         views.getAcademicLabel.as_view(), name='getAcademicLabel'),

    # Path for getting all academic labels after a certain year
    path('getAcademicLabelFromYearAll/<str:getYearTerm>/',
         views.getAcademicLabelFromYearAll.as_view(), name='getAcademicLabelFromYearAll'),

    # Path for getting all student types based on year terms
    path('getYearTerm/<str:getStudentType>/',
         views.getYearTerm.as_view(), name='getYearTerm'),

    # Path for getting all the academic types based on previos selections
    path('getAcademicType/<str:getStudentType>/<str:getYearTerm>/<str:getAcademicLabel>/',
         views.getAcademicType.as_view(), name='getAcademicType'),

    # Path for getting all the charts based on previous selection
    path('getPredictionData/<str:getStudentType>/<str:getYearTerm>/<str:getAcademicType>/',
         views.getPredictionData.as_view(), name='getPredictionData'),

    # Path for getting all the charts based on previous selection
    path('getSnapshotData/<str:getYearTerm>/<str:getAcademicType>/',
         views.getSnapshotData.as_view(), name='getSnapshotData'),

    path('getModifiedChartCohort/<str:numberOfStudents>/<str:sigma>/<str:alpha>/<str:beta>/<str:steady>/<str:higherEdId>',
         views.getModifiedChartCohort.as_view(), name='getModifiedChartCohort'),

    # Path for password reset
    path('account-reset-validate/verify-token/', views.CustomPasswordTokenVerificationView.as_view(),
         name='password_reset'),

    url('account-reset-validate/',
        include('django_rest_passwordreset.urls', namespace='account-reset-validate')),


    url('^', include('django.contrib.auth.urls')),

]
