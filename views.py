from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from serializers import *

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.generics import (
		CreateAPIView,
		DestroyAPIView,
		ListAPIView,
		UpdateAPIView,
		RetrieveAPIView,
		RetrieveUpdateAPIView,
	)
# from rest_framework.mixins import DestoryModelMixin, UpdataModelsMixin
# from rest_framework.permission import (
# 		AllowAny,
# 		IsAuthenticated,
# 		IsAdminUser,
# 		IsAuthenticatedOrReadOnly,
# 	)

# from posts.api.permissions import IsOwnerOrReadOnly
# from posts.api.permissions import PostLimitOffsetPagination, PostPageNumberPagination

class UserCreateApiview(CreateAPIView):
	serializer_class = UserCreateSerilizers
	queryset = User.objects.all()

class UserLoginApiview(APIView):
	# permissions_classes = [AllowAny]
	serializer_class = UserLoginSerializers

	def post(self, request, *args, **kwargs):
		data = request.data
		serializer = UserLoginSerializers(data=data)
		if serializer.is_valid(raise_exception=True):
			new_data = serializer.data
			return Response(new_data, status=HTTP_200_OK)
		return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

	
class BlogView(APIView):
	def get(self, request):
		data = []
		try:
			obj = Blog.objects.all().select_related('user')
			for item in obj:
				dict ={}
				dict['comment'] = item.comment
				dict['author'] = item.author
				dict['name'] = item.user.name
				dict['email_id'] = item.user.emailid
				dict['marks'] = item.user.marks
				dict['city'] = item.user.city
				dict['date'] = item.user.dat
				data.append(dict)
			if data:
				response = { 'Meta': {'status' : 'Success'}, 'data' : data}	
			else:
				response = { 'Meta': {'status' : 'Failure'}, 'Failure reason' : 'Data are not found', 'data' : data}
		except Exception as e:
			response = {'Meta': {'status': 'Failure'}, 'Failure reason': str(e)}
		return Response(response)