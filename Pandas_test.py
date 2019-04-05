from rest_framework.views import APIView
from dashapp.serializers import *
from django.shortcuts import render, HttpResponse
from rest_framework.authentication import SessionAuthentication 
from rest_framework.permissions import IsAuthenticated
from dashapp.views import AccessControl
import sys
import os
import pandas as pd
import numpy as np
from pandas import DataFrame

revenue_project_details  = os.getcwd() + "/7_NewPAR_Report.csv"

class RevenueProjectDetailsView(APIView):
	authentication_classes = (SessionAuthentication,)
	permission_classes = (IsAuthenticated,)

	def get(self, request, format=None):
		profile = AccessControl.getUserProfile(request.user.username)
		contractor_id = profile.contractor_id
		try:
			data_fields = ['Id', 'Title', 'Project Start', 'Project End', 'Customer Division', 'Customer Business Unit', 'Contractor Id']
			dataFrame = pd.read_csv(revenue_project_details, skipinitialspace=True, usecols=data_fields)
			details_splited = dataFrame.to_dict('records')
			response = json.dumps(details_splited, indent=4)
		except Exception as e:
			return HttpResponse(str(e), content_type='Application/json')
		return HttpResponse(response, content_type='Application/json')
