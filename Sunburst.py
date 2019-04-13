from dashapp.views import *
from django.db.models import Sum, Q

gpc_cube_actuals  = os.getcwd() + "/6_GPC_KBD_Cube_Actuals.csv"

class BarChartGraphViews(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        profile = AccessControl.getUserProfile(request.user.username)
        contractor_id = [profile.contractor_id]
        key = request.GET.get('key')
        response = json.dumps(self.create_sunburst_json(key, contractor_id), indent=4)
        return HttpResponse(response, content_type='Application/json')

    
    def create_sunburst_json(self, key, contractor_id):
        response_json = list()
        kbd_rule_data = KBDRule.objects.all()
        response_json.append(self.get_kbd_details(kbd_rule_data.filter(hierarchy__iexact=key).first(), contractor_id))
        for item in kbd_rule_data.filter(parent__startswith=key):
        	response_json.append( self.get_kbd_details(item, contractor_id))
        return response_json

    def get_kbd_details(self, record, contractor_id):
    	period_list = ['0.00'] * 12
    	total_value = 0.00
    	actual_list = list()
    	forecast_list = list()
    	try:
    		record_dict = dict()
	    	record_dict['name'] = record.kpi_name
	    	record_dict['parent'] = record.parent
	    	record_dict['id'] = record.hierarchy
	    	try:
	    		period_data = KBDPeriodDetails.objects.all().select_related('kbd_detail_id').filter(Q(kbd_detail_id__contractor_id__in=contractor_id))
	    		hierarchy_data = period_data.select_related('kbd_detail_id__kbd_rule_id').filter(kbd_detail_id__kbd_rule_id__hierarchy__startswith=record.hierarchy)
	    		autual_forecast = hierarchy_data.values('period').annotate(total=Sum('amount'))
	    		for item in autual_forecast:
	    			total_value += float(item['total'])
	    			act_data = "{0:,.0f}".format(item['total'])
	    			record_dict[item['period']] = act_data
	    	except Exception as e:
	    		raise ValueError("Failure Reason", str(e))
	    	record_dict['total'] = total_value
    	except Exception as e:
    		raise ValueError("Failure Reason: ", str(e))
    	return record_dict
