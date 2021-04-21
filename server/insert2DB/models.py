from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class HigherEdDatabase(models.Model):
    data = models.TextField(max_length=200)
    academicLabel = models.TextField(max_length=200)
    yearTerm = models.TextField(max_length=200)
    academicType = models.TextField(max_length=200)
    studentType = models.TextField(max_length=200)
    cohortDate = models.TextField(max_length=200)
    amountOfStudents = models.CharField(max_length=200)
    pubDate = models.DateTimeField('date published')

    # class Meta:
    #     unique_together = ("yearTerm", "academicType", "studentType")

    def __str__(self):
        return self.data

    def was_published_recently(self):
        return self.pubDate >= timezone.now() - datetime.timedelta(days=1)


class predictionType(models.Model):
    UniqueID = models.TextField(max_length=200)
    userProvider = models.TextField(max_length=200)
    typeOfData = models.TextField(max_length=200)
    sigma = models.FloatField()
    alpha = models.FloatField()
    beta = models.FloatField()
    lmbda = models.FloatField()
    numberOfStudents = models.IntegerField()
    pubDate = models.DateTimeField('date published')

    def __str__(self):
        return self.UniqueID

    def was_published_recently(self):
        return self.pubDate >= timezone.now() - datetime.timedelta(days=1)

# CONSUMER ROLES


class DepartmentConsumer(models.Model):
    class Meta:
        permissions = (("can_read_dpt", "Can read dpt"),)


class CollegeConsumer(models.Model):
    class Meta:
        permissions = (("can_read_clg", "Can read clg"),
                       ("can_read_dpt", "Can read dpt"),)


class UniversityConsumer(models.Model):
    class Meta:
        permissions = (("can_read_uni", "Can read uni"),
                       ("can_read_clg", "Can read clg"),
                       ("can_read_dpt", "Can read dpt"),)


class SystemConsumer(models.Model):
    class Meta:
        permissions = (("can_read_sys", "Can read sys"),
                       ("can_read_uni", "Can read uni"),
                       ("can_read_clg", "Can read clg"),
                       ("can_read_dpt", "Can read dpt"),)

# PROVIDER ROLES


class DepartmentProvider(models.Model):
    class Meta:
        permissions = (("can_write_dpt", "Can write dpt"),
                       ("can_read_dpt", "Can read dpt"),)


class CollegeProvider(models.Model):
    class Meta:
        permissions = (("can_write_clg", "Can write clg"),
                       ("can_write_dpt", "Can write dpt"),
                       ("can_read_dpt", "Can read dpt"),
                       ("can_read_clg", "Can read clg"),)


class UniversityProvider(models.Model):
    class Meta:
        permissions = (("can_write_uni", "Can write uni"),
                       ("can_write_clg", "Can write clg"),
                       ("can_write_dpt", "Can write dpt"),
                       ("can_read_dpt", "Can read dpt"),
                       ("can_read_clg", "Can read clg"),
                       ("can_read_uni", "Can read uni"),)


class SystemProvider(models.Model):
    class Meta:
        permissions = (("can_write_sys", "Can write sys"),
                       ("can_write_uni", "Can write uni"),
                       ("can_write_clg", "Can write clg"),
                       ("can_write_dpt", "Can write dpt"),
                       ("can_read_dpt", "Can read dpt"),
                       ("can_read_clg", "Can read clg"),
                       ("can_read_uni", "Can read uni"),
                       ("can_read_sys", "Can read sys"),)

# PROJECT OWNERS


class Developer(models.Model):
    class Meta:
        permissions = (("can_view_all", "Can view all"),)
