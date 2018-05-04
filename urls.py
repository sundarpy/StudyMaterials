from django.conf.urls import url
from ad_hoc_scripts.ad_hoc_scripts import *
from api_views import *

urlpatterns = [
    url(r'^getnews', GetNewsRecordView.as_view(),name="get_news_results"),
    url(r'^updatenewstactical', UpdateNewsView.as_view(),name="update_news_view"),
    url(r'^scorecalcultaions', ScoreCalculationsView.as_view(),name="score_calculations_view"),
    url(r'^updateintensitybyexecutive', UpdateIntensityView.as_view(),name="update_intersity_score_view"),
    url(r'^getsignalslist', SiganlListView.as_view(),name="signal_list_view"),
    url(r'^newscount', StateWiseNewsCount.as_view(),name="news_count_state_wise"),
    url(r'^get_news_records_for_tactical', GetNewsRecordsForTactical.as_view(),name="news_records_tactical"),
    url(r'^get_news_details_based_on_news_id', GetNewsDetailsBasedOnNewsid.as_view(),name="get_news_details_based_on_news_id"),
    url(r'^get_news_based_on_filter', GetNewsBasedOnFilter.as_view(),name="get_news_based_on_filter_view"),
    url(r'^update_verify_news', UpdateVerifyNews.as_view(),name="update_news_as_verify"),
    url(r'^data_bricks_job_call', DataBrickJobCallView.as_view(),name="data_bricks_job_call_view"),
    url(r'^validate_multiple_news', UpdateMultipleNews.as_view(),name="validate_multiple_news_view"),
    url(r'^update_state_to_unprocessed', UpdateStateToUnprocessed.as_view(),name="update_state_to_unprocessed_view"),
    url(r'^signal_oi_score_calculations', CalculateSignalOiScore.as_view(), name='signal-oi-score-view'),
    url(r'^executive_profiles_list', ExecutiveProfileList.as_view(), name='executive-profile-list-view'),
    url(r'^iris1_company_list', Iris1MasterCompanyList.as_view(), name='iris1-company-list-view'),

    # ad-hoc urls export_records_state_9,
    url(r'^convert_state_2_to_9_by_query', ConvertStateTo9ByQuery.as_view(),name="convert_2_state_to_9"),
    url(r'^get_records_state_9', GetRecordsState9.as_view(),name="get_records_state_9"),
    url(r'^export_records_state_9', ExpoortRecordsofState9.as_view(),name="export_state_9_records"),
    url(r'^update_signal_names_by_sheet', UpdateSignalsByCSV.as_view(),name="update_signal_names_by_sheet"),
]
