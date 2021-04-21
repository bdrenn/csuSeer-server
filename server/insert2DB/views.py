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
    filterCheck = HigherEdDatabase.objects.filter(yearTerm=request.data.get(
        'yearTermF'), academicType=request.data.get('academicTypeF'), studentType=request.data.get('studentTypeF'))
    if len(filterCheck) > 0:
        filterCheck = filterCheck[0]
        filterCheck.data = request.data.get('data')
        filterCheck.yearTerm = request.data.get('yearTermF')
        filterCheck.academicType = request.data.get('academicTypeF')
        filterCheck.studentType = request.data.get('studentTypeF')
        filterCheck.amountOfStudents = request.data.get('amountOfStudents')
        filterCheck.academicLabel = request.data.get('academicLabel')
        filterCheck.pubDate = timezone.now()
        filterCheck.save()
        return Response(filterCheck.id)
    newData = HigherEdDatabase(data=request.data.get('data'), yearTerm=request.data.get('yearTermF'), academicType=request.data.get('academicTypeF'), studentType=request.data.get(
        'studentTypeF'), cohortDate=request.data.get('cohortDate'), amountOfStudents=request.data.get('amountOfStudents'), academicLabel=request.data.get('academicLabel'), pubDate=timezone.now())
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
    print(schoolData)
    print(schoolData[0].studentType)
    isTransfer = True if schoolData[0].studentType == "TRANSFER" else False
    excelData = eval(schoolData[0].data)
    nStudents = int(request.data.get('amountOfStudents'))
    [sigma, beta, alpha, lmbd] = particleSwarmOptimization(
        request, nStudents, excelData, isTransfer)
    graph = cohortTrain(nStudents, sigma, beta, alpha,
                        isTransfer=isTransfer, isMarkov=False, steadyStateTrigger=False, excelData=excelData, retrieveX=False)

    # Check if entry in prediction type database already exists
    filterCheck = predictionType.objects.filter(
        UniqueID=uniqueID)
    # If we get a query back, we update the entry
    if len(filterCheck) > 0:
        filterCheck = filterCheck[0]
        filterCheck.sigma = sigma
        filterCheck.alpha = alpha
        filterCheck.beta = beta
        filterCheck.lmbda = lmbd
        filterCheck.numberOfStudents = nStudents
        filterCheck.pubDate = timezone.now()
        filterCheck.save()

    # Else just create a new entry
    else:
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
                           0.15, isTransfer=False, isMarkov=False, steadyStateTrigger=False, excelData={}, retrieveX=False)
        totalGraphs = {'NumOfFigures': len(data), 'Figures': data}
        # json_dump = json.dumps(totalGraphs, cls=NumpyEncoder)
        return Response(totalGraphs)

# Getting the options for charts


class getAcademicLabel(APIView):
    def get(self, request, getStudentType, getYearTerm):
        queryResult = HigherEdDatabase.objects.filter(
            studentType=getStudentType, yearTerm=getYearTerm).values('academicLabel').distinct()
        # data = HigherEdDatabase.objects.filter(studentType=studentType)
        return Response(list(queryResult))


class getAcademicLabelFromYear(APIView):
    def get(self, request, getYearTerm):
        queryResult = HigherEdDatabase.objects.filter(
            yearTerm__level__gte=getYearTerm).values('academicLabel').distinct()
        # data = HigherEdDatabase.objects.filter(studentType=studentType)
        return Response(list(queryResult))

# Filters the academic label for the snapshort charts


class getAcademicLabelFromYearAll(APIView):
    def get(self, request, getYearTerm):
        years_back = 5
        queried_data = []
        temp_list = []
        for i in range(1, years_back+1):
            fall_yearterm = "FALL " + str(int(getYearTerm) - i)
            spring_yearterm = "SPRING " + str(int(getYearTerm) - i)
            fall_list = list(HigherEdDatabase.objects.filter(
                yearTerm=fall_yearterm).values('academicLabel', 'academicType').distinct())
            spring_list = list(HigherEdDatabase.objects.filter(
                yearTerm=spring_yearterm).values('academicLabel', 'academicType').distinct())
            print(spring_yearterm)
            print(spring_list)
            if (fall_list != []):
                queried_data.append(fall_list)
            if (spring_list != []):
                queried_data.append(spring_list)
        print(queried_data)
        print(len(queried_data))
        return Response(queried_data)


class getYearTerm(APIView):
    # permission_classes = (IsAuthenticated, )
    def get(self, request, getStudentType):
        queryResult = HigherEdDatabase.objects.filter(
            studentType=getStudentType).values('yearTerm').distinct()
        # data = HigherEdDatabase.objects.filter(studentType=studentType)
        return Response(list(queryResult))

# class getYearTermAll(APIView):
#     def get(self, request):
#         queryResult = HigherEdDatabase.objects.filter().values('yearTerm').distinct()
#         # data = HigherEdDatabase.objects.filter(studentType=studentType)
#         return Response(list(queryResult))


class getAcademicType(APIView):
    # permission_classes = (IsAuthenticated, )
    def get(self, request, getStudentType, getYearTerm, getAcademicLabel):
        queryResult = HigherEdDatabase.objects.filter(studentType=getStudentType,
                                                      yearTerm=getYearTerm, academicLabel=getAcademicLabel).values('academicType').distinct()
        # data = HigherEdDatabase.objects.filter(studentType=studentType)
        print(list(queryResult))
        return Response(list(queryResult))


# Getting the prediction data and student numbers based on the user's input


class getPredictionData(APIView):
    def get(self, request, getStudentType, getYearTerm, getAcademicType):
        queryResult = HigherEdDatabase.objects.filter(studentType=getStudentType,
                                                      yearTerm=getYearTerm, academicType=getAcademicType).values('id')

        queryResultList = list(queryResult)
        higherEdId = ""
        if len(queryResultList) > 0:
            # Work on max for the id
            higherEdId = queryResultList[-1]['id']
        prediction = predictionType.objects.filter(UniqueID=higherEdId)
        # if len(queryPrediction) > 0:
        #     prediction = max(list(queryPrediction))
        excelData = HigherEdDatabase.objects.filter(id=higherEdId)
        isTransfer = True if excelData[0].studentType == 'TRANSFER' else False
        excelDataObj = eval(excelData[0].data)
        higherEdId = excelData[0].id
        data = cohortTrain(prediction[0].numberOfStudents, prediction[0].sigma,
                           prediction[0].alpha, prediction[0].beta, isTransfer=isTransfer, isMarkov=False, steadyStateTrigger=False, excelData=excelDataObj, retrieveX=False)
        totalGraphs = {'NumOfFigures': len(data), 'Figures': data, 'MetaData': {
            'numberOfStudents': prediction[0].numberOfStudents, 'sigma': prediction[0].sigma, 'alpha': prediction[0].alpha, 'beta': prediction[0].beta}, 'higherEdId': higherEdId}
        return Response(totalGraphs)


# Gets the graph data for the charts with the inputed data when manipulating a cohort
class getModifiedChartCohort(APIView):

    def get(self, request, numberOfStudents, sigma, alpha, beta, steady, higherEdId):
        queryResult = HigherEdDatabase.objects.filter(id=higherEdId)
        isTransfer = True if queryResult[0].studentType == 'TRANSFER' else False
        excelDataObj = eval(queryResult[0].data)
        tempBool = True if steady == "True" else False
        data = cohortTrain(int(numberOfStudents), float(sigma), float(alpha),
                           float(beta), isTransfer=isTransfer, isMarkov=False, steadyStateTrigger=tempBool, excelData=excelDataObj, retrieveX=False)

        totalGraphs = {'NumOfFigures': len(data), 'Figures': data, 'MetaData': {
            'numberOfStudents': numberOfStudents, 'sigma': sigma, 'alpha': alpha, 'beta': beta}}
        return Response(totalGraphs)

# This class we get a graph depending on the value given to the steady state (p)


class getSnapshotData(APIView):
    def get(self, request, getYearTerm, getAcademicType):
        years_back = 5
        # List of higher ed data for terms we have in the backend as objects
        term_list = []

        # List of all terms in the range of available terms as strings
        available_terms = []

        for i in range(years_back):
            fall_yearterm = "FALL " + str(int(getYearTerm) - years_back + i)
            spring_yearterm = "SPRING " + \
                str(int(getYearTerm) - years_back + i + 1)

            # Query for all fall terms based on the years back i,e. Fall 2016 - Fall 2021
            temp_fall_list_freshmen = list(HigherEdDatabase.objects.filter(
                yearTerm=fall_yearterm, academicType=getAcademicType, studentType='FRESHMEN').values('id', 'data', 'studentType', 'yearTerm').distinct())
            # Query for all spring terms based on the years back i,e. Fall 2016 - Fall 2021
            temp_spring_list_freshmen = list(HigherEdDatabase.objects.filter(
                yearTerm=spring_yearterm, academicType=getAcademicType, studentType='FRESHMEN').values('id', 'data', 'studentType', 'yearTerm').distinct())
            # Query for all fall terms based on the years back i,e. Fall 2016 - Fall 2021
            temp_fall_list_transfer = list(HigherEdDatabase.objects.filter(
                yearTerm=fall_yearterm, academicType=getAcademicType, studentType='TRANSFER').values('id', 'data', 'studentType', 'yearTerm').distinct())
            # Query for all spring terms based on the years back i,e. Fall 2016 - Fall 2021
            temp_spring_list_transfer = list(HigherEdDatabase.objects.filter(
                yearTerm=spring_yearterm, academicType=getAcademicType, studentType='TRANSFER').values('id', 'data', 'studentType', 'yearTerm').distinct())

            # These if statements check for empty queries in order to avoid them
            if (temp_fall_list_freshmen != []):
                available_terms.append(fall_yearterm)
                term_list.append(temp_fall_list_freshmen[0])

            if (temp_fall_list_transfer != []):
                available_terms.append(fall_yearterm)
                term_list.append(temp_fall_list_transfer[0])

            if (temp_spring_list_freshmen != []):
                available_terms.append(spring_yearterm)
                term_list.append(temp_spring_list_freshmen[0])

            if (temp_spring_list_transfer != []):
                available_terms.append(spring_yearterm)
                term_list.append(temp_spring_list_transfer[0])

        print(available_terms)

        # Query greek leetters and add them to prediction list
        prediction_list = []
        for higheredObj in term_list:
            prediction = predictionType.objects.filter(
                UniqueID=higheredObj['id']).values()
            prediction_list.append(list(prediction)[0])

        # We loop through the length all the semesters in available terms in order to get back the x values from the cohort model function
        for i in range(len(available_terms)):
            higherEd_obj = None
            prediction = None

            # Find a higher ed object in term list that matches our available terms
            # We might not need
            for term_list_index in range(len(term_list)):
                if term_list[term_list_index]['yearTerm'] == available_terms[i] and term_list_index == i:
                    higherEd_obj = term_list[term_list_index]
                    break

            # Find the matching prediction obj for the higher higher ed obj
            for term_prediction in prediction_list:
                if term_prediction['UniqueID'] == str(higherEd_obj["id"]):
                    prediction = term_prediction
                    break

            # Check whether the cohort is transfer or freshman
            transfer_bool = True if higherEd_obj['studentType'] == 'TRANSFER' else False
            print(higherEd_obj['studentType'])

            # We ran the cohort train function to get the x matrix
            x_data = cohortTrain(prediction['numberOfStudents'], float(prediction['sigma']), float(prediction['alpha']),
                                 float(prediction['beta']), isTransfer=transfer_bool, isMarkov=False, steadyStateTrigger=False, excelData=higherEd_obj['data'], retrieveX=True)

            x_data = list(x_data)

            if i == 0:
                first_x_data = x_data
                # Here for all the ranges now we go from 0 to 7 rather than 1 to 8
                for index in range(len(first_x_data)):
                    first_x_data[index] = list(first_x_data[index][0:])

            first_term = available_terms[0]

            if i != 0:
                av_term = available_terms[i]

                grab_first_year = int(
                    first_term[(len(first_term)-2): len(first_term)])
                grab_next_year = int(av_term[(len(av_term)-2): len(av_term)])

                padding_times = (2 * (grab_next_year-grab_first_year)
                                 ) if first_term[0] == available_terms[i][0] else 2 * (grab_next_year-grab_first_year) - 1

                print('is transfer or freshmen')
                print(transfer_bool)
                print('first term')
                print(first_term)
                print('next term')
                print(av_term)
                print('padding')
                print(padding_times)

                for times in range(padding_times):
                    for j in range(len(x_data)):
                        if times == 0:
                            # Here we want to access data at position j from 0: not 1:
                            x_data[j] = list(x_data[j][0:])
                        x_data[j].insert(0, 0)

                for index in range(len(first_x_data)):
                    for j in range(len(first_x_data[0])):
                        first_x_data[index][j] = first_x_data[index][j] + \
                            x_data[index][j]

        for index in range(len(first_x_data)):
            first_x_data[index] = np.array(first_x_data[index])

        # This portion creates the year term labels for the graph
        year_terms_labels = [available_terms[0]]
        year_fall = available_terms[0][len(
            available_terms[0])-2: len(available_terms[0])]
        year_spring = available_terms[0][len(
            available_terms[0])-2: len(available_terms[0])]

        for i in range(13):
            if year_terms_labels[i][0] == "F":
                year_spring = int(year_spring) + 1
                year_terms_labels.append("SPRING " + str(year_spring))
            else:
                if year_terms_labels[0] == "S" and i == 0:
                    year_terms_labels.append("FALL" + year_fall)
                else:
                    year_fall = int(year_fall) + 1
                    year_terms_labels.append("FALL " + str(year_fall))

        data = {'NumOfFigures': 2, 'Figures': {'figure2': {'x-axis': year_terms_labels, '0% achieved': (first_x_data[0], '#000000'), '12.5% achieved': (first_x_data[1], '#E69F00'),
                                                           '25% achieved': (first_x_data[2], '#56B4E9'), '37.5% achieved': (first_x_data[3], '#009E73'), '50% achieved': (first_x_data[4], '#F0E442'),
                                                           '62.5% achieved': (first_x_data[5], '#0072B2'), '75% achieved': (first_x_data[6], '#D55E00'), '87.5% achieved': (first_x_data[7], '#CC79A7'),
                                                           'description': ['Figure 1', 'Student Count in DCMs within University'], 'yLabel': 'Number of Students in Each Class'},
                                               'figure3': {'x-axis': year_terms_labels, '0% achieved': ((first_x_data[0] + first_x_data[1]) / 2, '#000000'),
                                                           '25% achieved': ((first_x_data[2] + first_x_data[3]) / 2, '#E69F00'),
                                                           '50% achieved': ((first_x_data[4] + first_x_data[5]) / 2, '#56B4E9'),
                                                           '75% achieved': ((first_x_data[6] + first_x_data[7]) / 2, '#009E73'), 'description': ['Figure2', ' Student Count in Super DCMs within University'],
                                                           'yLabel': 'Number of Students'}}}

        return Response(data)


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
