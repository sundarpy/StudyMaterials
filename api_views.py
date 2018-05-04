from __future__ import unicode_literals
from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import json,requests,urllib3,logging
from django.db.models import Case, When, BooleanField,Q
from signal_processing_constants import *
from functions import news_details_obj,flux_score_obj,master_obj,news_realted_obj,score_realted_obj
from serializers import TaggedNewsRecordSerilaizer,SignalListSerializer
from gateway.signal_processing.models import MasterCompany,TaggedNews, SignalLibrary,MetaStates, SignalOi
from gateway.pce.common.pceconstants import PCE_SOURCE_ID
from gateway.iris2.models import MasterSource
from gateway.pce.models.executive_view import ExecutiveView
from gateway.iris1.models import MasterCompany as IrisMasterCompany
logger = logging.getLogger("signal-processing-logger")

class GetNewsRecordView(APIView):
    """
        This View Returns Single News at a time to Dashboard Based on Company Name or Random Wise
        Ando Also STATE will be Changed To STATE_1 FROM STATE_0
        It will Change the State of Record,un processed to Sent To Dashboard State
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        """
            Returns The Record if any unprocessed records are available in the Database or else it will send the message
            like "No Records Found"
        """
        lists = []
        response = {'meta': {'status': 'failure','failure_reason': 'Something went wrong,please try again'}, 'data': 'No News are found'}
        news_records = None
        try:
            if "company_name" in request.data:
                company_record = master_obj.get_master_company_obj(request.data['company_name'],check_in_both=False)
                if company_record is not None:
                    news_records = TaggedNews.objects.filter(user=USER_FILTER,trans_thru_dt=MAX_DATE_TIME,
                                                             state=STATE_0, company_id=company_record.id,
                                                             publication_date__gte=PUBLICTION_GT_DATE).exclude(given_classification_id=19).order_by('-publication_date').first()

            else:
                news_records = TaggedNews.objects.filter(user=USER_FILTER,trans_thru_dt=MAX_DATE_TIME,
                                                         state=STATE_0,publication_date__gte=PUBLICTION_GT_DATE).exclude(given_classification_id=19).order_by('-publication_date').first()
            if news_records is not None:
                signal_records = SignalLibrary.objects.filter(signal_id=news_records.given_classification_id).first()
                news_record_data = TaggedNewsRecordSerilaizer(news_records).data
                news_record_data.pop('company')
                if news_record_data['oi_score'] is None:
                    news_record_data['oi_score'] = 0
                    news_record_data['total_oi_score'] = 0
                else:
                    news_record_data['total_oi_score'] = news_realted_obj.get_total_oi_score(news_record_data['oi_score'],signal_records[0].Weightage)
                data = { 'signal_id': signal_records.signal_id,
                         'signal_type': signal_records.signal_type,
                         'weightage': signal_records.Weightage }
                data.update(news_record_data)
                # if not signal_records.news_variable is None:
                #     temp_dict = dict((key, value) for key, value in news_record_data.iteritems() if
                #                      key in NEWS_VAR_LIST)
                #     lists.append([key for key in temp_dict if key not in signal_records.news_variable])
                #     [data.pop(i) for i in lists[0]]
                # else:
                #     [data.pop(i) for i in NEWS_VAR_LIST]
                news_records.state_id = MetaStates(state_id=STATE_1)
                news_records.save()
                if data:
                    response = {'meta': {'status': 'success'}, 'data': data}
                else:
                    response = {'meta': {'status': 'failure','failure_reason': 'No Records Found'}, 'data': data}
            else:
                response = {'meta': {'status': 'failure','failure_reason': 'No Records Found'}, 'data': 'No News are found'}
        except Exception as e:
            logger.exception(e.message)
            response = {'meta': {'status': 'failure','failure_reason': str(e)}, 'data': 'No records are found'}
        return Response(response)


class UpdateNewsView(APIView):
    """
        Accepts Data From Dashboard and Updates the record with new Calculations
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        response = {'meta': {'status': 'failure','failure_reason': 'Something went wrong,please try again',}, 'data': 'Not updated'}
        if "state" not in request.data and "final_classification" not in request.data and "news_id" not in request.data:
            response = {"meta":{"status":"failure","failure_reason":"key are not found in the request","data":"Not Updated"}}
        elif request.data["final_classification"] is None:
            response = {"meta": {"status": "failure", "failure_reason": "Signal Name Should Not be empty","data": "Not Updated"}}
        else:
            signal = request.data["final_classification"]
            final_classification_records = SignalLibrary.objects.filter(signal_name=signal)
            check_columns_flag,signal_keys = news_realted_obj.check_columns_validation(request.data,final_classification_records)
            news_records = TaggedNews.objects.filter(news_id=request.data['news_id'],trans_thru_dt=MAX_DATE_TIME).first()
            if "undefined" in request.data:
                request.data.pop('undefined')
            demo_dict = {'weightage': request.data.pop('weightage'),'total_oi_score': request.data.pop('total_oi_score')}
            if news_records is not None and check_columns_flag == True:
                request_state_id = request.data.pop("state")
                state_records = MetaStates.objects.filter(state_id=request_state_id).first()
                with transaction.atomic():
                    if 'Validated_Correct' in request.data:
                        request.data['Validated_Correct'] = news_realted_obj.get_validate_flag(request)
                    verify_state = MetaStates.objects.get(value__iexact='Verified')
                    validate_state = MetaStates.objects.get(value='validated')
                    signal_type = request.data['signal_type']
                    if request_state_id == STATE_2:
                        if news_records.state_id == validate_state.state_id:
                            request.data['Validated_Correct'] = True
                            request.data['state_id'] = verify_state
                        elif news_records.state_id == verify_state.state_id:
                            request.data['Validated_Correct'] = True
                            request.data['state_id'] = verify_state
                        else:
                            request.data['state_id'] = state_records.state_id
                        #PREPARE Save Tagged News Obj
                        data, master_company_records = news_realted_obj.get_saving_obj(request.data, final_classification_records)
                        [data.pop(element) for element in ['signal_id', 'signal_type', 'id'] if element in data]
                        #Update Tagged News and Create one with Latest
                        tagged,exception = news_realted_obj.update_and_save_tagged_news(data, news_records)
                        if tagged is not None:
                            if signal_type.lower() == 'strategic':
                                news_realted_obj.update_signal_oi(news_records.id)
                                news_realted_obj.save_signal_oi({"id":tagged.id,"trans_from_dt":data["trans_from_dt"]}, demo_dict, final_classification_records[0].refresh_rate)
                            if signal.lower() == 'executive movement':
                                if master_company_records:
                                    library_flux_score = flux_score_obj.update_library_flux_score(signal, master_company_records.id)
                            response = {'meta': {'status': 'success'}, 'data': "successfully updated"}
                        else:
                            response = {'meta': {'status': 'failure','failure_reason': str(exception)}, 'data': 'Not updated'}
                    else:
                        if news_records.state_id == verify_state.state_id:
                            if request_state_id == STATE_6:
                                if signal_type in SIGNAL_TYPE_LIST:
                                    # PREPARE Save Tagged News Obj
                                    data, master_company_records = news_realted_obj.get_saving_obj(request.data,final_classification_records)
                                    if signal.lower() == 'executive movement':
                                        if master_company_records:
                                            library_flux_score = flux_score_obj.update_library_flux_score(signal,master_company_records.id)

                                    data['state_id'] = verify_state.state_id
                                    data['Validated_Correct'] = True
                                    data['comments'] = 'corrected by ' + request.data['user']
                                    data['trans_from_dt'] = datetime.datetime.now()
                                    data['trans_thru_dt'] = MAX_DATE_TIME
                                    poped_elements = {element: data.pop(element) for element in ['signal_id','signal_type','id']
                                                      if element in data}
                                    #SAVE AND UPDATE THE NEWS RECORD
                                    tagged_new_obj,exception = news_realted_obj.update_and_save_tagged_news(data,news_records)
                                    if tagged_new_obj is not None:
                                        if 'signal_type' in poped_elements:
                                            if poped_elements['signal_type'].lower() == 'strategic':
                                                news_realted_obj.update_signal_oi(news_records.id)
                                                tagged_new_obj.refresh_from_db()
                                                tagged_dict = {'id': tagged_new_obj.id,'trans_from_dt': tagged_new_obj.trans_from_dt}
                                                news_realted_obj.save_signal_oi(tagged_dict, demo_dict,final_classification_records[0].refresh_rate)
                                    else:
                                        response = {'meta': {'status': 'failure', 'failure_reason': str(exception)},'data': 'Not updated'}
                                else:
                                    news_realted_obj.update_to_veriy_news(request,news_records,verify_state,final_classification_records)
                                    news_realted_obj.update_signal_oi(news_records.id)
                            else:
                                news_realted_obj.update_to_veriy_news(request, news_records, verify_state,final_classification_records)
                                news_realted_obj.update_signal_oi(news_records.id)
                        else:
                            news_records.state_id = state_records.state_id
                            news_records.user = request.data['user']
                            if 'Validated_Correct' in request.data:
                                news_records.Validated_Correct = request.data['Validated_Correct']
                            if request_state_id == STATE_6 and signal_type == 'strategic':
                                news_records.oi_score = request.data['oi_score']
                                news_records.intensity = request.data['intensity']
                                news_realted_obj.save_signal_oi({'id': news_records.id, 'trans_from_dt': news_records.trans_from_dt}, demo_dict,
                                               final_classification_records[0].refresh_rate)
                                if signal.lower() == 'executive movement':
                                    master_company_records = master_obj.get_master_company_obj(request.data['company_name'],check_in_both=True)
                                    if master_company_records:
                                        library_flux_score = flux_score_obj.update_library_flux_score(signal,master_company_records.id)
                            else:
                                news_realted_obj.update_signal_oi(news_records.id)
                            news_records.save()
                        response = {'meta': {'status': 'success'}, 'data': "successfully updated"}
            else:
                if not check_columns_flag:
                    response = {'meta': {'status': 'failure', 'failure_reason': 'mandatory keys are missing',"mandatory_keys":signal_keys},'data': 'Not updated'}
                else:
                    response = {'meta': {'status': 'failure','failure_reason': 'No records Found',}, 'data': 'Not updated'}
        return Response(response)

class ScoreCalculationsView(APIView):
    """
    calculate the oi score for the record and returns related records as well
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        # TODO:Have to calculate score for Financial
        data = request.data
        total_news_records = []
        total_number_of_pages = 0
        signal = request.data['signal'].lower()
        if signal == 'executive movement':
            total_score = score_realted_obj.executive_movement_score(data)
        elif signal == "mass hiring":
            total_score = score_realted_obj.mass_hiring_score(data)
        elif signal == "layoff":
            total_score = score_realted_obj.lay_off_score(data)
        elif signal == 'pe majority stake buy':
            total_score = score_realted_obj.pe_investment_score(data)
        # elif signal=="Financial Activity":
        #     financial_score(data)
        elif signal == "mergers and acquisitions":
            total_score = score_realted_obj.mergers_acquisitions_score(data)
        elif signal == "deal renewal":
            total_score = score_realted_obj.deal_renewal_score(data)
        else:
            total_score = score_realted_obj.get_dummy_score(signal)
        intens = score_realted_obj.update_score(data, total_score)
        company_details = news_realted_obj.get_company_records(data)
        if company_details:
            records = company_details.order_by('id')
            number_of_records_per_page = Paginator(records, 15)
            total_number_of_pages = number_of_records_per_page.num_pages
            pages = number_of_records_per_page.page(request.GET.get('page_number'))
            news_records_per_page = pages.object_list
            total_news_records = news_details_obj.get_names_of_foreignkeys(news_records_per_page)
        return Response({'meta': {'status': 'success'}, 'data': intens,
            'news_records_based_on_company': total_news_records, 'total_number_of_pages': total_number_of_pages,
            'current_page': request.GET.get('page_number')})

class UpdateIntensityView(APIView):
    """
        It Returns the Oi Score of partucular News
    """
    def post(self,request,format=None):
        response = {'meta': {'status': 'failure','failure_reason': 'Something went wrong,please try again'},"data":"No Data"}
        try:
            news_details = TaggedNews.objects.filter(news_id=request.data['news_id'],trans_thru_dt=MAX_DATE_TIME).first()
            if news_details is not None:
                signal = SignalLibrary.objects.filter(signal_name=request.data['signal'])
                if request.data['intensity'] == '0':
                    response = {'meta': { 'status': 'success'}, 'data': {'intensity': '0', 'oi_score': 0, 'total_oi_score': 0,'weigthage': signal[0].Weightage}}
                else:
                    oi_score = score_realted_obj.get_new_oi_score(request.data, news_details.intensity, signal, news_details.oi_score)
                    if oi_score is None:
                        response = {"meta":{"status":"failure","failure_reason":"Oi Score is Empty"},"data":"Unable to calculate the Oi Score of this News"}
                    else:
                        response = {'meta': {'status': 'success'},
                                'data': {'oi_score': oi_score, 'intensity': request.data['intensity'], 'weigthage': signal[0].Weightage,
                                'total_oi_score': news_realted_obj.get_total_oi_score(oi_score,signal[0].Weightage)}}

            else:
                response = {'meta': { 'status': 'failure', 'failure_reason': 'failure'}, 'data': 'Not updated'}
        except Exception as e:
            logger.exception(e.message)
            response = {'meta': { 'status': 'failure','failure_reason': str(e)}, 'data': 'Not updated'}
        return Response(response)

class SiganlListView(APIView):
    """
        it returns all the signals and related variables
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, format=None):
        """
        """
        return Response({'meta': {'status': 'success'},"data":SignalListSerializer({}).data})

class StateWiseNewsCount(APIView):
    """
        Returns Count of Each and Every State of Tagged News
        Based on Given Dates,it will sends the results
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        lists = []
        if "to_date" in request.data and "from_date" in request.data:
            to_date = datetime.datetime.strptime(request.data['to_date'], '%Y-%m-%d') + datetime.timedelta(days=1)
            from_date = request.data['from_date']
            date_filter = True
        else:
            date_filter = False
        try:
            states_records = MetaStates.objects.all()
            for i in states_records:
                if date_filter:
                    news_count = TaggedNews.objects.filter(state=i.state_id,trans_from_dt__range=(from_date,to_date),trans_thru_dt=MAX_DATE_TIME).count()
                else:
                    news_count = TaggedNews.objects.filter(state=i.state_id,trans_thru_dt=MAX_DATE_TIME).count()
                data = {'state_name': i.value,'no_of_news': news_count}
                lists.append(data)
            if lists:
                response = {'meta': {'status': 'success'}, 'data': lists}
            else:
                response = {'meta': {'status': 'failure','failure_reason': 'No Records Found'}, 'data': lists}
        except Exception as e:
            logger.exception(e.message)
            response = {'meta': {'status': 'failure','failure_reason': str(e)}, 'data': str(e)}
        return Response(response)

class GetNewsRecordsForTactical(APIView):
    """"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        news_list = []
        try:
            next_date = datetime.date.today() + datetime.timedelta(days=1)
            date_before_10_days = next_date - datetime.timedelta(days=10)
            signal_records = SignalLibrary.objects.get(signal_name__iexact=request.data['signal_name'])
            signal_company_records = master_obj.get_master_company_obj(request.data["company_name"],check_in_both=False)
            if signal_company_records is not None:
                news_records = TaggedNews.objects.filter(company_id=signal_company_records.id,
                                                         trans_thru_dt=MAX_DATE_TIME,
                                                         trans_from_dt__range=(date_before_10_days, next_date),
                                                         state=STATE_2).annotate(
                    order_by_signal=Case(When(final_classification_id__exact=signal_records.signal_id, then=1), default=0,
                                         output_field=BooleanField())).order_by('-order_by_signal')
                if news_records:
                    records = news_records.order_by('id')
                    number_of_records_per_page = Paginator(records, 15)
                    total_number_of_pages = number_of_records_per_page.num_pages
                    pages = number_of_records_per_page.page(request.GET.get('page_number'))
                    news_records_per_page = pages.object_list
                    total_news_records = news_details_obj.get_names_of_foreignkeys(news_records_per_page)
                    response = {'meta': { 'status': 'success'},
                                'news_records_based_on_company': total_news_records, 'total_number_of_pages': total_number_of_pages,
                                'current_page': request.GET.get('page_number')}
                else:
                    response = {'meta': {'status': 'success',}, 'news_records_based_on_company': news_list}
            else:
                response = {'meta': {'status': 'failure',}, 'data': 'company name is not present'}
        except Exception as e:
            response = {'meta': {'status': 'failure','failure_reason': str(e)}, 'data': str(e)}
        return Response(response)


class GetNewsDetailsBasedOnNewsid(RetrieveAPIView):
    """It Returns News Detail Object """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        try:
            news_id = request.GET.get('news_id')
            news_records = TaggedNews.objects.filter(news_id=news_id,trans_thru_dt=MAX_DATE_TIME)
            total_records = news_details_obj.get_names_of_foreignkeys(news_records)
            response = {'meta': { 'status': 'success',}, 'news_based_on_filter': total_records}
        except Exception as e:
            response = {'meta': { 'status': 'failure',}, 'news_based_on_filter': str(e)}
        return Response(response)

class GetNewsBasedOnFilter(APIView):
    """"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        try:
            if 'download_all' in request.data:
                query_set = TaggedNews.objects.all().exclude(given_classification_id=19)
                number_of_records_per_page = Paginator(query_set.order_by('-publication_date'), 50)
            else:
                query_set = TaggedNews.objects.filter(trans_thru_dt=MAX_DATE_TIME).exclude(given_classification_id=19)
                if 'user_name' in request.data:
                    request.data['user'] = request.data.pop('user_name')
                filter_attributes = {key + '__in': request.data[key] for key in request.data.keys() if
                                     key in ['state', 'user']}
                if 'news_id' in request.data:
                    filter_attributes['news_id'] = request.data['news_id']

                if "data_extraction_flag" in request.data:
                    filter_attributes['data_extraction_flag'] = request.data['data_extraction_flag']

                filter_attributes["publication_date__gte"] = PUBLICTION_GT_DATE
                if filter_attributes:
                    query_set = query_set.filter(**filter_attributes)

                if 'company_name' in request.data:
                    signal_company_id = master_obj.get_master_company_ids(request.data['company_name'])
                    query_set = query_set.filter(company_id__in=signal_company_id)
                if 'from_date' in request.data:
                    final_date = request.data['to_date'] if 'to_date' in request.data else str(datetime.date.today())
                    to_date = datetime.datetime.strptime(final_date, '%Y-%m-%d')
                    query_set = query_set.filter(publication_date__range=(request.data['from_date'], to_date + datetime.timedelta(days=1)))
                if 'signal_type' in request.data:
                    query_set = query_set.filter(final_classification__signal_type__in=request.data['signal_type'])
                if 'verification_state' in request.data:
                    validated_state = [(True if i.lower() == 'correct' else (False if i.lower() == 'incorrect' else None))
                                       for i in request.data['verification_state']]
                    query_set1 = None
                    if None in validated_state:
                        query_set1 = query_set.filter(Validated_Correct__isnull=True)
                        validated_state.remove(None)
                    query_set2 = query_set.filter(Validated_Correct__in=validated_state)
                    if query_set1:
                        query_set = query_set1 | query_set2
                    else:
                        query_set = query_set2
                if 'tagging_from_date' in request.data:
                    final_tagging_date = request.data['tagging_to_date'] if 'tagging_to_date' in request.data \
                        else str(datetime.date.today())
                    tagging_to_date = datetime.datetime.strptime(final_tagging_date, '%Y-%m-%d')
                    query_set = query_set.filter(trans_from_dt__range=(request.data['tagging_from_date'],
                                                                   tagging_to_date + datetime.timedelta(days=1)))
                if 'category' in request.data:
                    query_set = query_set.filter(final_classification__signal_name__in=request.data['category'])

                # records = query_set.order_by('news_id')
                number_of_records_per_page = Paginator(query_set.order_by('-publication_date'), 15)

            if {'min_range', 'max_range'}.issubset(request.data.keys()):
                lists = []
                for page_number in range(request.data['min_range'], request.data['max_range'] + 1):
                    page_records = number_of_records_per_page.page(page_number)
                    single_records = page_records.object_list
                    lists.extend(single_records)

                new_number_of_records_per_page = Paginator(lists, 60)
                total_number_of_pages = new_number_of_records_per_page.num_pages
                pages = new_number_of_records_per_page.page(request.GET.get('page_number'))
                total_news_records = news_details_obj.get_names_of_foreignkeys(pages.object_list)
            else:
                total_number_of_pages = number_of_records_per_page.num_pages
                pages = number_of_records_per_page.page(request.GET.get('page_number'))
                total_news_records = news_details_obj.get_names_of_foreignkeys(pages.object_list)
            return Response({'meta': {
                'status': 'success',
            }, 'news_based_on_filter': total_news_records,
                'total_number_of_pages': total_number_of_pages,
                'current_page': request.GET.get('page_number'),
                'total_number_of_records': query_set.count(),
                'all_records_count': TaggedNews.objects.all().count()})
        except Exception as e:
            return Response({'meta': {
                'status': 'Failure',
                'failure_reason': str(e)
            }})

class UpdateVerifyNews(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        try:
            news_records = TaggedNews.objects.filter(news_id=request.data['news_id'],trans_thru_dt=MAX_DATE_TIME).first()
            user_name = request.data.pop('user_name')
            if 'comments' not in request.data:
                request.data['comments'] = "validated by user " + user_name

            if news_records is not None:
                request.data['Validated_Correct'] = news_realted_obj.get_validate_flag(request)
                with transaction.atomic():
                    news_realted_obj.update_signal_oi(news_records.id)
                    news_records.trans_thru_dt = datetime.datetime.now()
                    news_records.save()
                    news_records.pk = None
                    news_records.trans_thru_dt = MAX_DATE_TIME
                    news_records.trans_from_dt = datetime.datetime.now()
                    news_records.state_id = MetaStates.objects.get(value__iexact='Verified')
                    news_records.Validated_Correct = request.data['Validated_Correct']
                    news_records.comments = request.data['comments']
                    news_records.user = user_name
                    news_records.save()
                news_records.refresh_from_db()
                final_classification_records = SignalLibrary.objects.filter(signal_id=news_records.final_classification_id
                                                                            ).first()
                if final_classification_records is not None:
                    if final_classification_records.signal_type.lower() == 'strategic':
                        total_o_i_score =news_realted_obj.get_total_oi_score(news_records.oi_score,final_classification_records.Weightage)
                        news_dict = {'id': news_records.id, 'trans_from_dt': news_records.trans_from_dt}
                        total_oi_dict = {'total_oi_score': total_o_i_score}
                        news_realted_obj.save_signal_oi(news_dict, total_oi_dict, final_classification_records.refresh_rate)
                        if final_classification_records.signal_name.lower() == 'executive movement':
                            master_company_records = MasterCompany.objects.filter(id=news_records.company_id).first()
                            if master_company_records:
                                library_flux_score = flux_score_obj.update_library_flux_score(final_classification_records.signal_name, master_company_records.id)
                total_news_records = news_details_obj.get_single_foreign_key_names(news_records)
                response = {'meta': {'status': 'success',}, 'data': total_news_records}
            else:
                response = {'meta': {'status': 'failure','failure_reason': 'No Records Found'}, 'data': "not updated"}

        except Exception as e:
            response = {'meta': {'status': 'failure','failure_reason': str(e)}, 'data': "not updated"}
        return Response(response)

class DataBrickJobCallView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        try:
            urllib3.disable_warnings()
            url = 'https://dbc-a2b10b4a-cd7b.cloud.databricks.com/api/2.0/jobs/run-now'
            values = {'job_id': request.GET.get('job_id')}
            headers = {'Authorization': 'Bearer ' + 'dapi0f7353f6d3155a41396f66ca476421b3'}
            r = requests.post(url, data=json.dumps(values), headers=headers)
            r.connection.close()
            response = r.json(())
        except Exception as e:
            logger.exception(e.message)
            response = str(e)
        return Response(response)


class UpdateMultipleNews(APIView):
    """"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        news_lists = request.data['news_list']
        failed_news_ids,success_news_ids = [],[]
        try:
            for news_id in news_lists:
                news_records = TaggedNews.objects.filter(news_id=news_id,trans_thru_dt=MAX_DATE_TIME).first()
                if news_records is None:
                    failed_news_ids.append(news_id)
                else:
                    news_records.state_id = MetaStates.objects.get(value__iexact='Verified')
                    news_records.Validated_Correct = True
                    news_records.comments = "bulk validated by " + request.data['user_name']
                    news_records.save()
                    success_news_ids.append(news_id)
            response = {'meta': {'status': "success"},"failed_news_ids":failed_news_ids,"success_news_ids":success_news_ids, 'data': "successfully updated"}
        except Exception as e:
            logger.exception(e.message)
            response = {'meta': {'status': "failure"}, 'data': str(e)}
        return Response(response)


class UpdateStateToUnprocessed(APIView):
    """
    It will Change the state of all records which are in "sent to dashbaord" state to unprocessed
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        news_realted_obj.state_to_unprocessed()
        return Response("successfully updated")

class CalculateSignalOiScore(APIView):
    """
        calculate signal oi score for tagged news
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        """
            Calculate and Save the oi score into signal oi model
        """
        failed_records,dummy_score_records = [],[]
        data = request.data
        if "start" in data.keys() and "end" in data.keys():
            tagged_news = TaggedNews.objects.filter(id__gte=data['start'],id__lte=data['end'],
                trans_thru_dt=MAX_DATE_TIME,
                Validated_Correct=True, state_id=STATE_9,final_classification_id__in=SignalLibrary.objects.filter(signal_type__iexact=STRATEGIC).values_list('signal_id', flat=True))
        elif "id" in data.keys():
            tagged_news = TaggedNews.objects.filter(id=data['id'],
                                                    trans_thru_dt=MAX_DATE_TIME,
                                                    Validated_Correct=True, state_id=STATE_9,final_classification_id__in=SignalLibrary.objects.filter(signal_type__iexact=STRATEGIC).values_list('signal_id', flat=True))
        elif "news_id" in data.keys():
            tagged_news = TaggedNews.objects.filter(news_id=data['news_id'],
                                                    trans_thru_dt=MAX_DATE_TIME,
                                                    Validated_Correct=True, state_id=STATE_9,final_classification_id__in=SignalLibrary.objects.filter(signal_type__iexact=STRATEGIC).values_list('signal_id', flat=True))
        else:
            tagged_news = TaggedNews.objects.filter(trans_thru_dt=MAX_DATE_TIME,
                                                   Validated_Correct=True,state_id=STATE_9,
                                                    final_classification_id__in=SignalLibrary.objects.filter(signal_type__iexact=STRATEGIC).values_list('signal_id', flat=True))

        for news_record in tagged_news:
            total_oi_score_data = news_realted_obj.getOiScore(news_record)
            if total_oi_score_data['dummy'] == True:
                dummy_score_records.append({news_record.id:news_record.news_id})
            signal_save_flag = news_realted_obj.save_signal_oi({"id":news_record.id,"trans_from_dt":news_record.trans_from_dt},total_oi_score_data,news_record.final_classification.refresh_rate)
            if signal_save_flag == False:
                failed_records.append({news_record.id:news_record.news_id})

        return Response({'meta': {'status': 'success'},"dummy_score_records":dummy_score_records,"failed_records":failed_records,"message":"successfully calculated oi scores"})



class ExecutiveProfileList(APIView):
    """
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        """"""
        response = {"meta":{"status":"Failure"},"data":"No Records Found","message":"Something went wrong,please try again"}
        try:
            source = MasterSource.objects.get(id=PCE_SOURCE_ID).source_name
            fields = ["executive_id", "executive_name","public_profile_link","designation", "organization"]
            query = 'SELECT executive_id,executive_name,public_profile_link,designation,organization FROM pce_executiveview WHERE data_source_name="{}"'.format(source)
            if "search_str" in request.data:
                if len(request.data["search_str"].strip()) > 0:
                    query += ' AND LOWER(executive_name)  LIKE "%{}%"'.format(request.data["search_str"].strip().lower())
                cursor = master_obj.get_db_connection(PCE_DB_NAME)
                if cursor is not None:
                    cursor.execute(query)
                    row = cursor.fetchall()
                    data = [{"executive_id": i[0], "executive_name": i[1], "public_profile_link": i[2], "designation": i[3],
                      "organization": i[4]} for i in row]
                    master_obj.close_db_connection(cursor)
                else:
                    logger.info("Not able to get the connection from Database")
                    data = ExecutiveView.objects.filter(data_source_name=source).values(*fields)[0:100]
            else:
                data = ExecutiveView.objects.filter(data_source_name=source).values(*fields)[0:100]
            response = {"meta":{"status":"Success"},"data":data}
        except Exception as e:
            logger.exception(e.message)
        return Response(response)


class Iris1MasterCompanyList(APIView):
    """
    It Returns Top 500 MVP Company Names from iris1.0 database
    if any search keyword provide from search ,will be given results based on search params
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self,request,format=None):
        response = {"data":[],"meta":{"status":"failure"}}
        if "search_str" not in request.data:
            data = IrisMasterCompany.objects.filter().values_list('company_name', flat=True)[0:500]
            response = {"data":data,"meta":{"status":"success"}}
        else:
            data = IrisMasterCompany.objects.filter(company_name__icontains=request.data["search_str"]).values_list('company_name', flat=True)[0:500]
            response = {"data": data, "meta": {"status": "success"}}
        return Response(response)


