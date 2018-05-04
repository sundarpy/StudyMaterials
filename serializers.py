from rest_framework import serializers
import ast,pdb
from gateway.signal_processing.models import TaggedNews, SignalLibrary, LevelRatingLibrary, BusinessFunctionLibrary, \
    GeographyLibrary, SignalPerformanceLibrary, DealRenewalLocation, MovementFluxLibrary,MasterCompany


class TaggedNewsSerializer(serializers.ModelSerializer):
    other_columns = serializers.SerializerMethodField()
    class Meta:
        model = TaggedNews
        fields = '__all__'

    def get_other_columns(self,obj):
        try:
            other_columns = ast.literal_eval(obj.other_columns)
        except Exception as e:
            other_columns = ""
            print(e)
        return other_columns


class TaggedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaggedNews
        fields = ['url', 'news_id', 'trans_from_dt', 'intensity', 'publication_date', 'oi_score']


class TaggedNewsRecordSerilaizer(TaggedNewsSerializer):
    """"""
    final_classification = serializers.SerializerMethodField()
    given_classification = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()
    new_level = serializers.SerializerMethodField()
    bussiness_function = serializers.SerializerMethodField()
    geography = serializers.SerializerMethodField()
    deal_renewal_location_records = serializers.SerializerMethodField()
    movement_flux = serializers.SerializerMethodField()
    performance = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    class Meta:
        model = TaggedNews
        fields = '__all__'

    def get_final_classification(self,obj):
        signal_name = None
        if obj.final_classification is not None:
            signal_name = obj.final_classification.signal_name
        return signal_name
    def get_given_classification(self,obj):
        signal_name = None
        if obj.given_classification is not None:
            signal_name = obj.given_classification.signal_name
        return signal_name
    def get_driver(self,obj):
        driver = None
        if obj.driver is not None:
            driver = obj.driver.driver
        return driver

    def get_new_level(self,obj):
        level = None
        if obj.new_level is not None:
            level = obj.new_level.levels
        return level
    def get_bussiness_function(self,obj):
        bussiness_function = None
        if obj.bussiness_function is not None:
            bussiness_function = obj.bussiness_function.business_functon
        return bussiness_function
    def get_geography(self,obj):
        geography = None
        if obj.geography is not None:
            geography = obj.geography.region
        return geography

    def get_deal_renewal_location_records(self,obj):
        deal_renewal_location_records = None
        if obj.deal_renewal_location_records is not None:
            deal_renewal_location_records = obj.deal_renewal_location_records.deal_location
        return deal_renewal_location_records
    def get_movement_flux(self,obj):
        movement_flux = None
        if obj.movement_flux is not None:
            movement_flux = obj.movement_flux.announcement_type
        return movement_flux
    def get_performance(self,obj):
        performance = None
        if obj.performance is not None:
            performance = obj.performance.performance
        return performance
    def get_company_name(self,obj):
        company_name = None
        if obj.company is not None:
            company_name = obj.company.mvp_company_name
        return company_name

class SignalListSerializer(serializers.Serializer):
    """
    """
    signal = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    business = serializers.SerializerMethodField()
    geography = serializers.SerializerMethodField()
    signal_performance_records = serializers.SerializerMethodField()
    deal_renewal_location_records = serializers.SerializerMethodField()
    low_level =  serializers.SerializerMethodField()
    medium_level = serializers.SerializerMethodField()
    high_level = serializers.SerializerMethodField()
    movement_flux = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    companies_list = serializers.SerializerMethodField()
    movement_status = serializers.SerializerMethodField()
    data_extraction_flag = serializers.SerializerMethodField()

    def get_signal(self, obj):return SignalLibrary.objects.all().values()
    def get_level(self,obj):return LevelRatingLibrary.objects.all().values()
    def get_business(self,obj):return BusinessFunctionLibrary.objects.all().values()
    def get_geography(self,obj):return GeographyLibrary.objects.all().values()
    def get_signal_performance_records(self,obj):return SignalPerformanceLibrary.objects.all().values()
    def get_deal_renewal_location_records(self,obj):return DealRenewalLocation.objects.all().values()
    def get_low_level(self,obj):return ['Yes', 'No']
    def get_data_extraction_flag(self,obj):return [True,False]
    def get_medium_level(self, obj): return ['Yes', 'No']
    def get_high_level(self, obj): return ['Yes', 'No']
    def get_movement_status(self,obj):return ["Joined","Left"]
    def get_movement_flux(self,obj):return MovementFluxLibrary.objects.all().values()
    def get_user_name(self,obj):return TaggedNews.objects.values_list('user', flat=True).distinct()
    def get_companies_list(self,obj):return MasterCompany.objects.all().distinct().values_list('mvp_company_name', flat=True)
