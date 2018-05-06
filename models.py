from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=50)
    emailid = models.EmailField(max_length=50)
    marks = models.IntegerField(default=0, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    dat = models.DateField(auto_now=True)
    user = models.IntegerField(primary_key=True)

    def __str__(self): # unicode(self)
            return self.emailid

class Blog(models.Model):
	user = models.ForeignKey(Student, on_delete=models.CASCADE)
	author = models.CharField(max_length=20)
	comment = models.TextField(max_length=255)
	dat1 = models.DateField(auto_now=True)

	def __unicode__(self):
		return self.comment