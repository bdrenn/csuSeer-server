from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType
from .models import HigherEdDatabase, predictionType, User, DepartmentConsumer, CollegeConsumer, UniversityConsumer, SystemConsumer, DepartmentProvider, CollegeProvider, UniversityProvider, SystemProvider, Developer
from lotus.cohortModel import cohortTrain
from lotus.pso import particleSwarmOptimization
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
import numpy as np
from django.core.mail import EmailMessage
from django.dispatch import receiver
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.views import get_password_reset_token_expiry_time
from django_rest_passwordreset.signals import reset_password_token_created
from rest_framework import parsers, renderers, status
from .serializer import CustomTokenSerializer
from django.urls import reverse
from datetime import timedelta

# This function creates a new entry in the auth_user collection in the database


@api_view(["POST"])
def createUser(request):
    user = User.objects.create_user(username=request.data.get(
        'username'), email=request.data.get('email'), password=request.data.get('password'))
    # TODO Send email to user upon registering
    success = "User created successfully"
    return Response(success)


'''
TODO Fix permissions
'''
# Give permissions to a user


@api_view(["POST"])
def givePerm(request):
    print(request)
    print("unit_level")
    print(request.data.get('unit_level'))
    username = request.data.get('username')
    password = request.data.get('password')
    # NEED TO GET SPECIAL KEY FROM USER##############JSON TOKEN FROM SCHOOL MAYBE?
    user = authenticate(username=username, password=password)
    if user is not None:
        access = request.data.get('unit_level')
        content_type = ContentType.objects.get_for_model(eval(access))
        print("content_type")
        print(content_type)
        all_permissions = Permission.objects.filter(content_type=content_type)
        print('all_perms')
        print(all_permissions)
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

# Filters a speficic student type, year term and academic type from an uploaded excel and insierts it to the database HigherEdDataBase


@api_view(["POST"])
def uploadFile(request):
    # Filter to check if the entry exists or not (1 or 0)
    filterCheck = HigherEdDatabase.objects.filter(yearTerm=request.data.get(
        'yearTermF'), academicType=request.data.get('academicTypeF'), studentType=request.data.get('studentTypeF'))
    # If length is greater than 0, replace the entry with the new data
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
    # Otherwise create and save the new entry in the HigherEdDatabse collection
    newData = HigherEdDatabase(data=request.data.get('data'), yearTerm=request.data.get('yearTermF'), academicType=request.data.get('academicTypeF'), studentType=request.data.get(
        'studentTypeF'), cohortDate=request.data.get('cohortDate'), amountOfStudents=request.data.get('amountOfStudents'), academicLabel=request.data.get('academicLabel'), pubDate=timezone.now())
    newData.save()
    # The unique id of the new entry will be used to create an entry in the predictiontype collection
    uniqueID = newData.id
    return Response(uniqueID)

# Trains the selection of the uploaded file and updates existing entries with the new training data i.e. alpha, beta, sigma


@api_view(["POST"])
def trainModel(request):
    uniqueID = request.data.get('uniqueID')
    schoolData = HigherEdDatabase.objects.filter(id=uniqueID)
    isTransfer = True if schoolData[0].studentType == "TRANSFER" else False
    excelData = eval(schoolData[0].data)
    nStudents = int(request.data.get('amountOfStudents'))
    # Calls the particleSawrmOptimization function to retrieve sigma, alpha, beta and lmbda
    [sigma, beta, alpha, lmbd] = particleSwarmOptimization(
        request, nStudents, excelData, isTransfer)
    # Uses the greek letters to train it and get a graph of the trained data
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
    # TODO check if this else is needed
    else:
        newdata = predictionType(UniqueID=uniqueID, sigma=sigma, alpha=alpha,
                                 beta=beta, lmbda=lmbd, numberOfStudents=nStudents, pubDate=timezone.now())
        newdata.save()
    return Response(graph)

# Getting the academic labels for dropdown selection for charts based on student type and academic year
# i.e. academic labels are plan name(major), deparment, college, university


class getAcademicLabel(APIView):
    def get(self, request, getStudentType, getYearTerm):
        queryResult = HigherEdDatabase.objects.filter(
            studentType=getStudentType, yearTerm=getYearTerm).values('academicLabel').distinct()
        return Response(list(queryResult))

# Getting the academic labels for dropdown selection for snapshot charts based only on years_back
# i.e. academic labels are plan name(major), deparment, college, university


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
            if (fall_list != []):
                queried_data.append(fall_list)
            if (spring_list != []):
                queried_data.append(spring_list)
        return Response(queried_data)


# Getting the year term for dropdown selection for charts based on student type
# i.e. Spring 2021, Fall 2021

class getYearTerm(APIView):
    def get(self, request, getStudentType):
        queryResult = HigherEdDatabase.objects.filter(
            studentType=getStudentType).values('yearTerm').distinct()
        return Response(list(queryResult))

# Getting the academic type for dropdown selection for charts based on student type, year term and academic label
# i.e. For academic plan (major) Pre-Computer Science, Mechanical Enginering, etc


class getAcademicType(APIView):
    # permission_classes = (IsAuthenticated, )
    def get(self, request, getStudentType, getYearTerm, getAcademicLabel):
        queryResult = HigherEdDatabase.objects.filter(studentType=getStudentType,
                                                      yearTerm=getYearTerm, academicLabel=getAcademicLabel).values('academicType').distinct()
        # data = HigherEdDatabase.objects.filter(studentType=studentType)
        print(list(queryResult))
        return Response(list(queryResult))


# Gets the prediction type for charts i.e. greek letters and number of students

class getPredictionData(APIView):
    def get(self, request, getStudentType, getYearTerm, getAcademicType):
        queryResult = HigherEdDatabase.objects.get(studentType=getStudentType,
                                                   yearTerm=getYearTerm, academicType=getAcademicType)

        higherEdId = queryResult.id
        prediction = predictionType.objects.get(UniqueID=higherEdId)
        excelData = HigherEdDatabase.objects.get(id=higherEdId)
        # Eval is needed to convert the string with the excel data from HigherEdDatabase
        # TODO: have a collection for the data column on HigherEdDatabase
        excelDataObj = eval(excelData.data)
        isTransfer = True if excelData.studentType == 'TRANSFER' else False
        higherEdId = excelData.id
        data = cohortTrain(prediction.numberOfStudents, prediction.sigma,
                           prediction.alpha, prediction.beta, isTransfer=isTransfer, isMarkov=False, steadyStateTrigger=False, excelData=excelDataObj, retrieveX=False)
        # Formats the charts data for the front end
        totalGraphs = {'NumOfFigures': len(data), 'Figures': data, 'MetaData': {
            'numberOfStudents': prediction.numberOfStudents, 'sigma': prediction.sigma, 'alpha': prediction.alpha, 'beta': prediction.beta}, 'higherEdId': higherEdId}
        return Response(totalGraphs)


# Gets the graph data for the charts with the inputed data when updating greek values, number of students and steady strigger

class getModifiedChartCohort(APIView):
    def get(self, request, numberOfStudents, sigma, alpha, beta, steady, higherEdId):
        queryResult = HigherEdDatabase.objects.get(id=higherEdId)
        isTransfer = True if queryResult.studentType == 'TRANSFER' else False
        # Eval is needed to convert the string with the excel data from HigherEdDatabase
        # TODO: have a collection for the data column on HigherEdDatabase
        excelDataObj = eval(queryResult.data)
        tempBool = True if steady == "True" else False
        data = cohortTrain(int(numberOfStudents), float(sigma), float(alpha),
                           float(beta), isTransfer=isTransfer, isMarkov=False, steadyStateTrigger=tempBool, excelData=excelDataObj, retrieveX=False)

        # Formats the modified charts data for the front end
        totalGraphs = {'NumOfFigures': len(data), 'Figures': data, 'MetaData': {
            'numberOfStudents': numberOfStudents, 'sigma': sigma, 'alpha': alpha, 'beta': beta}}
        return Response(totalGraphs)

# Returns all the data of the last 'years_back' as a single graph


class getSnapshotData(APIView):
    def get(self, request, getYearTerm, getAcademicType):
        years_back = 5

        # List of 'HigherEdDatabase' rows for available terms in the database
        term_list = []

        # List of all terms in the database given by the range of 'years_back'
        available_terms = []

        for i in range(years_back):
            # Constructs a string of terms given by the range of 'years_back'
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

        # Query greek letters and add them to prediction list, indexes in prediction_list match the indexes in term_list
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
            for term_list_index in range(len(term_list)):
                if term_list[term_list_index]['yearTerm'] == available_terms[i] and term_list_index == i:
                    higherEd_obj = term_list[term_list_index]
                    break

            # Find the matching prediction obj for the 'HigherEdDatabase' object
            for term_prediction in prediction_list:
                if term_prediction['UniqueID'] == str(higherEd_obj["id"]):
                    prediction = term_prediction
                    break

            # Check whether the cohort is transfer or freshman
            transfer_bool = True if higherEd_obj['studentType'] == 'TRANSFER' else False

            # Call 'cohortTrain' function to get the x matrix by passing True for the 'retrieveX' parameter
            x_data = cohortTrain(prediction['numberOfStudents'], float(prediction['sigma']), float(prediction['alpha']),
                                 float(prediction['beta']), isTransfer=transfer_bool, isMarkov=False, steadyStateTrigger=False, excelData=higherEd_obj['data'], retrieveX=True)

            x_data = list(x_data)

            # First iteration the numpy values inside x_data get converted into a list
            if i == 0:
                first_x_data = x_data
                for index in range(len(first_x_data)):
                    first_x_data[index] = list(first_x_data[index][0:])

            # Oldest available term (used to know how many times we need to pad the inner lists in the x_data list)
            first_term = available_terms[0]

            if i != 0:
                av_term = available_terms[i]

                # We grab the year from the first available term i.e. '20' from 'Fall 20'
                grab_first_year = int(
                    first_term[(len(first_term)-2): len(first_term)])

                # We grab the year from the remaining terms i.e. '20' from 'Fall 20'
                grab_next_year = int(av_term[(len(av_term)-2): len(av_term)])

                # Calculate how many times we pad i.e. Spring 20 and Spring 21 => 2 semester difference, and Fall 2019 Spring 2021 => 3 semester difference
                # first_term[0] will always be 'F' and for available_terms[0] could be 'S' or 'F'
                # TODO: check what would happpen if the first available term is a spring term instead of fall we might get a padding_times of -1
                padding_times = (2 * (grab_next_year-grab_first_year)
                                 ) if first_term[0] == available_terms[i][0] else 2 * (grab_next_year-grab_first_year) - 1
                # Will fix
                if padding_times == -1:
                    padding_times = 1
                # Loops the value of padding_times and pads every sublist inside x_data
                for times in range(padding_times):
                    for j in range(len(x_data)):
                        # For the first iteration the numpy arrays are casted to list
                        if times == 0:
                            x_data[j] = list(x_data[j][0:])
                        x_data[j].insert(0, 0)

                # After padding the elements in a sublist the sublisted get added
                # i.e. [[0, 1, 2], [3, 4, 5]] , [[6, 7, 8], [9, 10, 11]] into [[6, 8, 10], [12, 14, 16]]
                for index in range(len(first_x_data)):
                    for j in range(len(first_x_data[0])):
                        first_x_data[index][j] = first_x_data[index][j] + \
                            x_data[index][j]

        # Initialize a list with 16 zeros
        total_enrollment = [0] * 16

        # Adds the values from every sublists in first_x_data to calculate the total enrollment
        for index in range(len(first_x_data)):
            for j in range(len(first_x_data[0])):
                total_enrollment[j] = total_enrollment[j] + \
                    first_x_data[index][j]

        # Convert sublists back into numpy arrays in order to calculate the values for figure 3 (we can't add and divide lists)
        for index in range(len(first_x_data)):
            first_x_data[index] = np.array(first_x_data[index])

        # This portion creates the year term labels for the graph
        # Initialize year term labels as a list with the first available term
        year_terms_labels = [available_terms[0]]
        # Grab the first available fall term year
        year_fall = available_terms[0][len(
            available_terms[0])-2: len(available_terms[0])]
        # Grab the first available spring term year
        year_spring = available_terms[0][len(
            available_terms[0])-2: len(available_terms[0])]

        # Generate 14 semester labels for the x axsis
        for i in range(13):
            # Check if term is F (Fall)
            if year_terms_labels[i][0] == "F":
                # Add one to the year and append the next semester
                year_spring = int(year_spring) + 1
                year_terms_labels.append("SPRING " + str(year_spring))
            # If the first term is S (Spring)
            else:
                # Check first term is S (spring)
                if year_terms_labels[i][0] == "S" and i == 0:
                    year_terms_labels.append("FALL" + year_fall)
                # If first term is not spring
                else:
                    year_fall = int(year_fall) + 1
                    year_terms_labels.append("FALL " + str(year_fall))

        # Formats the snapshot charts data for the front end
        data = {'NumOfFigures': 3, 'Figures': {'figure2': {'x-axis': year_terms_labels, '0% achieved': (first_x_data[0], '#000000'), '12.5% achieved': (first_x_data[1], '#E69F00'),
                                                           '25% achieved': (first_x_data[2], '#56B4E9'), '37.5% achieved': (first_x_data[3], '#009E73'), '50% achieved': (first_x_data[4], '#F0E442'),
                                                           '62.5% achieved': (first_x_data[5], '#0072B2'), '75% achieved': (first_x_data[6], '#D55E00'), '87.5% achieved': (first_x_data[7], '#CC79A7'),
                                                           'description': ['Figure 1', 'Student Count in DCMs within University'], 'yLabel': 'Number of Students in Each Class'},
                                               'figure3': {'x-axis': year_terms_labels, '0% achieved': ((first_x_data[0] + first_x_data[1]) / 2, '#000000'),
                                                           '25% achieved': ((first_x_data[2] + first_x_data[3]) / 2, '#E69F00'),
                                                           '50% achieved': ((first_x_data[4] + first_x_data[5]) / 2, '#56B4E9'),
                                                           '75% achieved': ((first_x_data[6] + first_x_data[7]) / 2, '#009E73'), 'description': ['Figure2', ' Student Count in Super DCMs within University'],
                                                           'yLabel': 'Number of Students'},

                                               'figure1': {'x-axis': year_terms_labels, 'total_enrollment': (total_enrollment, '#000000'),
                                                           'description': ['Figure 3', 'Total enrollment within University '], 'yLabel': 'Number of Students'}

                                               }}

        return Response(data)


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
