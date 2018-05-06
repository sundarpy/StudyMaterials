from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework.serializers import (
	CharField,
	EmailField,
	ModelSerializer,
	ValidationError
	)

# class UserCreateSerilizers(ModelSerializer):
# 	# email = EmailField(label="Email Address")
# 	# email2 = EmailField(label="Confirm Email")


# 	class Meta:
# 		model = User
# 		fields = ('username', 'email', 'password')
# 		extra_kwargs = {"password":{"read_only": True}}

# 	def validate(self, data):
# 		email = data["email"]
# 		user_qs = User.objects.filter(email=email)
# 		if user_qs.exists():
# 			raise ValidationError("This user has already Registered.")
# 		return data

	# def validate_email(self, value):
	# 	data = self.get_initial()
	# 	email1 = data.get("email2")
	# 	email2 = value

	# 	if email1 != email2:
	# 		raise ValidationError("Email must match.")

	# 	user_qs = User.objects.filter(email=email)
	# 	if user_qs.exists():
	# 		raise ValidationError("This user has already Registered.")

	# 	return value

	# def create(self, validate_data):
	# 	username = validate_data["username"]
	# 	email = validate_data["email"]
	# 	password = validate_data["password"]

	# 	user_obj = User(username=username, email=email)

	# 	user_obj.set_password(password)
	# 	user_obj.save()
	# 	return validate_data




class UserLoginSerializers(ModelSerializer):
	token = CharField(allow_blank=True, read_only=True)
	username =  CharField(required=False, allow_blank=True)
	email = EmailField(label='Email Address', required=False, allow_blank=True)

	class Meta:
		model = User
		fields = ('username', 'email', 'password', 'token')
		extra_kwargs ={'password':{'write_only': True}}

	def validate(self, data):
		user_obj = None
		email = data.get('email')
		username = data.get('username')
		password = data['password']
		if not email and not username:
			raise ValidationError("A username or email is required to login")
		user = User.objects.filter(
				Q (email=email) |
				Q (username=username)
			).distinct()
		user = user.exclude(email__isnull=True).exclude(email__iexact='')
		print user
		if user.exists() and user.count() == 1:
			user_obj = user.first()
		else:
			raise ValidationError("This username/email is not valid.")
		if user_obj:
			if not user_obj.check_password(password):
				raise ValidationError("Incorrect Password please try again")

		data["token"] = "some random random token."
		return data

class UserCreateSerilizers(ModelSerializer):
	class Meta:
		model = User
		fields = ('username', 'email', 'password')

		extra_kwargs = {"password":{'write_only':True}}

	def create(self, validated_data):
		username = validated_data["username"] 
		email = validated_data["email"]
		password = validated_data["password"]
		user_obj = User(
				username = username,
				email = email
			)
		user_obj.set_password(password)
		user_obj.save()

		return validated_data

	def validate(self, data):
		email = data["email"]
		user_qs = User.objects.filter(email=email)
		if user_qs.exists():
			raise ValidationError("This Email has already Registered.")
		return data
