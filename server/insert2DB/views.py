from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType
from .models import HigherEdDatabase, predictionType, User, DepartmentConsumer, CollegeConsumer, UniversityConsumer, SystemConsumer, DepartmentProvider, CollegeProvider, UniversityProvider, SystemProvider, Developer
from lotus.cohortModel import cohortTrain
from lotus.pso import particleSwarmOptimization
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.utils import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import json
import numpy as np
import io
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

from django.dispatch import receiver
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.views import get_password_reset_token_expiry_time
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework import parsers, renderers, status
from .serializer import CustomTokenSerializer
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import timedelta

""" Classes for the views that will be rendered in Angular.js

    These files are saved in the static folder and then they are accessed
    through the template folder which as the index.html file.

    Args:
        request (object): The object sent with the request
        kwargs (dictionary): The different variables from angular.js
    Returns:
        a render request to the index.html file as mentioned above
"""


class HomePageView(APIView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)


class ChartsView(APIView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)


class LoginView(APIView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)


class RegisterView(APIView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)


class ProfileView(APIView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)


class UploadView(APIView):
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)


""" Classes for the routes that will be used by the frontend to do some action

    These routes will need to be locked behind various permissions and at the very
    least will need json web token authenication (from the IsAuthenticated library).

    Args:
        request (object): The object sent with the request
        incomingstudents (string): Amount of students incoming for a single semester
    Returns:pip i
        a response to the frontend with either a success message or a needed variable
"""

# Send email to user


@api_view(["POST"])
def sendEmail(request):
    subject = 'Email from backend of csuMarkov'
    message = 'This email was sent from the back end.\n Hehe I am glad it works.'
    from_email = settings.EMAIL_HOST_USER
    # to_list = ['lisa.star@csulb.edu', 'mehrdad.aliasgari@csulb.edu']
    to_list = ['diegocburela@gmail.com']
    send_mail(subject, message, from_email, to_list, fail_silently=False)
    success = "User emailed successfully"
    return Response(success)

# Creating a user


@api_view(["POST"])
def createUser(request):
    user = User.objects.create_user(username=request.data.get(
        'username'), email=request.data.get('email'), password=request.data.get('password'))

    # _email = request.data.get('email')
    # # Send email to new registered user
    # msg = EmailMessage(
    #     # title:
    #     "Welcome to the CSUSeer platform",
    #     # message:
    #     email_plaintext_message,
    #     # from:
    #     "csuseer2021@gmail.com",
    #     # to:
    #     [_email]
    # )
    # msg.send()

    success = "User created successfully"
    return Response(success)

# Give permissions to a user


@api_view(["POST"])
def givePerm(request):
    username = request.data.get('username')
    password = request.data.get('password')
    # NEED TO GET SPECIAL KEY FROM USER##############JSON TOKEN FROM SCHOOL MAYBE?
    user = authenticate(username=username, password=password)
    if user is not None:
        access = request.data.get('unit_level')
        content_type = ContentType.objects.get_for_model(eval(access))
        all_permissions = Permission.objects.filter(content_type=content_type)
        user.user_permissions.set(all_permissions)
        print(user.has_perm('insert2DB.can_write_sys'))
        return Response("success")
    else:
        success = "Permission was a failure :("
        return Response(success)

# Get permissions


@api_view(["POST"])
def getPerm(request):
    permission_list = []
    username = request.data.get('username')
    password = request.data.get('password')
    # NEED TO GET SPECIAL KEY FROM USER##############JSON TOKEN FROM SCHOOL MAYBE?
    user = authenticate(username=username, password=password)
    if user is not None:
        for p in Permission.objects.filter(user=user):
            permission_list.append(p.codename)
    else:
        permission_list = "failure :("
    return Response(permission_list)

# Getting all the universities saved in the DB


class index(APIView):
    permission_classes = (IsAuthenticated, "can_view_clg")

    def get(self, request):
        latestDataList = Data.objects.order_by('-pubDate')
        output = ', '.join([a.schoolName for a in latestDataList])
        return Response(output)

# Getting the data from a single university


class singleData(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, collegeName, departmentName):
        try:
            data = HigherEdDatabase.objects.get(
                collegeName=schoolName, departmentName=departmentName)
            output = str(data)
            return Response(output)
        except Data.DoesNotExist:
            data = "Oops! The data you're looking for does not exist."
            return Response(data)
        except Data.MultipleObjectsReturned:
            data = "Oops! That request returned too many responses."
            return Response(data)

# Getting multiple


class multipleData(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, collegeName):
        data = HigherEdDatabase.objects.filter(collegeName=schoolName)
        if not data:
            output = "There is no school under that name"
        else:
            output = ', '.join([a.departmentName for a in data])
        return HttpResponse(output)

# Upload new data for a school in collection


@api_view(["POST"])
def uploadFile(request):
    # HigherEdDataBase is the raw records provided by the users
    print(request.data.get('data'))
    newData = HigherEdDatabase(data=request.data.get('data'), collegeName=request.data.get('collegeName'), departmentName=request.data.get('departmentName'), universityName=request.data.get(
        'universityName'), cohortDate=request.data.get('cohortDate'), amountOfStudents=request.data.get('amountOfStudents'), pubDate=timezone.now())
    newData.save()
    # MAKING THE "BLANK" MODEL FOR WHEN WE WANT TO SAVE PREDICTIONS
    uniqueID = newData.id
    # blankPrediction = predictionType(UniqueID = uniqueID)
    # blankPrediction.save()
    return Response(uniqueID)

# Train a model on the newly updated school data


@api_view(["POST"])
def trainModel(request):
    uniqueID = request.data.get('uniqueID')
    schoolData = HigherEdDatabase.objects.filter(id=uniqueID)
    gradList = eval(schoolData[0].data)
    nStudents = int(request.data.get('amountOfStudents'))
    [sigma, beta, alpha, lmbd] = particleSwarmOptimization(
        request, nStudents, gradList)
    graph = cohortTrain(nStudents, sigma, beta, alpha,
                        isTransfer=False, isMarkov=False)
    #schoolData = predictionType.objects.filter(UniqueID = uniqueID)
    newdata = predictionType(UniqueID=uniqueID, sigma=sigma, alpha=alpha,
                             beta=beta, lmbda=lmbd, numberOfStudents=nStudents, pubDate=timezone.now())
    newdata.save()
    return Response(graph)


@ api_view(["POST"])
def saveModel(request):
    # ACTUALLY SAVE THE MODEL DATA HERE
    success = "need to actually change this to happen when success training"
    return Response(success)

# A class for changing variables to a json object.... not really used right now


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class testData(APIView):  # gradRate
    # Send a schools test data to the oracle
    def get(self, request, incomingStudents):
        data = cohortTrain(incomingStudents, 0.02, 0.05,
                           0.15, isTransfer=False, isMarkov=False)
        totalGraphs = {'NumOfFigures': len(data), 'Figures': data}
        # json_dump = json.dumps(totalGraphs, cls=NumpyEncoder)
        return Response(totalGraphs)


@ api_view(["POST"])
def passwordResetRequest(request):
    email_ = request.data.get('email')
    if(User.objects.filter(email=email_).count()):
        success = "Temporary response from backend!"
        print("User exists..")
        msg = EmailMessage('Request Callback',
                           'Here is the message.', to=[email_])
        msg.send()
        return Response(something)

    else:
        success = "Not successful"
        print("User does not exist..")
    print("Request is: ")
    print(request.data.get('email'))
    return Response(success)


class CustomPasswordResetView:
    @ receiver(reset_password_token_created)
    def password_reset_token_created(sender, reset_password_token, *args, **kwargs):
        """
          Handles password reset tokens
          When a token is created, an e-mail needs to be sent to the user
        """
        email_plaintext_message = "Follow the link to reset the password for your CSUSeer account, http://localhost:4200{}?token={} Thank you!".format(
            reverse('account-reset-validate:reset-password-request'), reset_password_token.key)
        msg = EmailMessage(
            # title:
            "Password Reset for {title}".format(title="CSUSeer"),
            # message:
            email_plaintext_message,
            # from:
            "csuseer2021@gmail.com",
            # to:
            [reset_password_token.user.email]
        )
        msg.send()


class CustomPasswordTokenVerificationView(APIView):
    """
      An Api View which provides a method to verifiy that a given pw-reset token is valid before actually confirming the
      reset.
    """
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser,
                      parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # After serializing we have the token
        token = serializer.validated_data['token']

        # get token validation time
        password_reset_token_validation_time = get_password_reset_token_expiry_time()

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(
            key=token).first()

        if reset_password_token is None:
            return Response({'status': 'invalid'}, status=status.HTTP_404_NOT_FOUND)

        # check expiry date
        expiry_date = reset_password_token.created_at + \
            timedelta(hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            return Response({'status': 'expired'}, status=status.HTTP_404_NOT_FOUND)

        # check if user has password to change
        if not reset_password_token.user.has_usable_password():
            return Response({'status': 'irrelevant'})

        return Response({'status': 'OK'})
