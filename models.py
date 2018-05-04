from __future__ import unicode_literals

# Create your models here.

from django.db import models
from django.db.models.signals import post_save
from gateway.pce.external_functions import etl_executive_obj
from django.utils import timezone

from gateway.iris2.common.validators import validate_company_name, validate_length


class SignalLibrary(models.Model):
    class Meta:
        unique_together = (('signal_name', 'signal_id'),)
        db_table = 'signal_library'

    signal_name = models.CharField(max_length=30)
    signal_id = models.AutoField(primary_key=True)
    signal_type = models.CharField(max_length=20, null=True)
    news_variable = models.TextField(blank=True)
    driver_variables = models.TextField(blank=True)
    Weightage = models.FloatField(null=True)
    refresh_rate = models.IntegerField(null=True)

    def __unicode__(self):
        return str(self.signal_id)


class MasterCompany(models.Model):
    company_name = models.CharField(max_length=200, unique=True, blank=True, null=True,
                                    validators=[validate_company_name, validate_length(200, "Company Name")])
    mvp_company_name = models.CharField(max_length=200, unique=True, blank=True, null=True,
                                        validators=[validate_company_name, validate_length(200, "Company Name")])
    website_domain = models.TextField(null=True, blank=True)

    def __int__(self):
        return self.id


class TaggedNews(models.Model):
    class Meta:
        unique_together = ['news_id', 'trans_thru_dt']
        db_table = 'tagged_news'

    news_id = models.CharField(max_length=50)
    summary = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    publication_date = models.DateTimeField(null=True, blank=True)
    url = models.CharField(max_length=200, null=True, blank=True)
    news_description = models.TextField(null=True, blank=True)
    company_name = models.TextField(null=True, blank=True)
    company = models.ForeignKey(MasterCompany, null=True, blank=True)
    source = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=200, null=True, blank=True)
    given_classification = models.ForeignKey('SignalLibrary', null=True, blank=True,
                                             related_name='given_classification')
    final_classification = models.ForeignKey('SignalLibrary',null=True,blank=True, related_name='final_classification')
    trans_from_dt = models.DateTimeField(null=True, blank=True)
    trans_thru_dt = models.DateTimeField(default=timezone.make_aware(timezone.datetime.max,
                                                                     timezone.get_default_timezone()))
    user = models.CharField(max_length=100, null=True, blank=True, default='machine')
    oi_score = models.DecimalField(null=True, max_digits=6, decimal_places=3, blank=True)
    state = models.ForeignKey('MetaStates', null=True, blank=True)
    driver = models.ForeignKey('DriverScoreLibrary', null=True, blank=True)
    new_level = models.ForeignKey('LevelRatingLibrary', null=True, blank=True)
    bussiness_function = models.ForeignKey('BusinessFunctionLibrary', null=True, blank=True)
    geography = models.ForeignKey('GeographyLibrary', null=True, blank=True)
    intensity = models.CharField(max_length=10, null=True, blank=True)
    company_invested_in = models.CharField(max_length=100, null=True, blank=True)
    performance = models.ForeignKey('SignalPerformanceLibrary', null=True, blank=True)
    deal_size = models.IntegerField(null=True, blank=True)
    deal_renewal_location_records = models.ForeignKey('DealRenewalLocation', null=True, blank=True)
    movement_flux = models.ForeignKey('MovementFluxLibrary', null=True, blank=True)
    high_level = models.CharField(max_length=5, null=True, blank=True)
    low_level = models.CharField(max_length=5, null=True, blank=True)
    medium_level = models.CharField(max_length=5, null=True, blank=True)
    Validated_Correct = models.BooleanField()
    comments = models.TextField()

    # weightage = models.IntegerField()

    #adding excutive name and executive id
    executive_name = models.CharField(max_length=250, null=True, blank=True)
    executive_id = models.CharField(max_length=50, null=True, blank=True)
    other_columns = models.TextField(blank=True)
    pipeline_status = models.IntegerField(default=0,null=False)
    data_extraction_flag = models.BooleanField(default=False)



    def __int__(self):
        return self.id


class BusinessFunctionLibrary(models.Model):
    business_functon = models.CharField(max_length=30, blank=True, null=True)
    score = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)

    class Meta:
        db_table = 'business_function_library'

    def __int__(self):
        return self.id


class DriverScoreLibrary(models.Model):
    driver = models.CharField(max_length=30, blank=True, null=True)
    score = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)

    class Meta:
        db_table = 'driver_score_library'

    def __int__(self):
        return self.id


class GeographyLibrary(models.Model):
    region = models.CharField(max_length=20, blank=True, null=True)
    score = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)

    class Meta:
        db_table = 'geography_library'

    def __int__(self):
        return self.id


class LevelRatingLibrary(models.Model):
    levels = models.CharField(max_length=30, blank=True, null=True)
    score = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)

    class Meta:
        db_table = 'level_rating_library'

    def __int__(self):
        return self.id


class SignalIntensityWeightsLibrary(models.Model):
    signal = models.OneToOneField(SignalLibrary)
    low_max_value = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)
    medium_min_value = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)
    medium_max_value = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)
    high_min_value = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=3)

    class Meta:
        db_table = 'signal_intensity_weights_library'


class SignalPercentageWeightLibrary(models.Model):
    signal = models.OneToOneField(SignalLibrary)
    percentage_weight = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'signal_percentage_weight_library'


class StockPerformanceLibrary(models.Model):
    performance = models.CharField(max_length=20, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'stock_performance_library'


class MetaStates(models.Model):
    state_id = models.IntegerField(primary_key=True)
    value = models.CharField(max_length=20, null=True)

    class Meta:
        db_table = 'meta_states'

    def __int__(self):
        return self.state_id


class SignalOi(models.Model):
    news = models.ForeignKey('TaggedNews', on_delete=models.CASCADE)
    oi_score = models.DecimalField(null=True, max_digits=6, decimal_places=3, blank=True)
    from_dt = models.DateTimeField(null=True)
    expiry_date = models.DateField(null=True)
    thru_date = models.DateTimeField(default=timezone.make_aware(timezone.datetime.max,
                                                                 timezone.get_default_timezone()))
    incremental_score = models.DecimalField(null=True, max_digits=6, decimal_places=3, blank=True)
    final_oi = models.DecimalField(null=True, max_digits=6, decimal_places=3, blank=True)

    class Meta:
        db_table = 'signal_oi'


class SignalPerformanceLibrary(models.Model):
    performance = models.CharField(max_length=20, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'signal_performance_library'

    def __int__(self):
        return self.id


class DealRenewalLocation(models.Model):
    deal_location = models.CharField(max_length=50, null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'deal_renewal_location'

    def __int__(self):
        return self.id


class MovementFluxLibrary(models.Model):
    announcement_type = models.CharField(max_length=20)
    score = models.IntegerField()

    class Meta:
        db_table = 'movement_flux_library'

    def __int__(self):
        return self.id




def etl_executive_movement(sender, instance, **kwargs):
    """if news is related to executive movement,we are inserting data to etl executive movement"""
    if "created" in kwargs and kwargs["created"] == True:
        if instance.data_extraction_flag==True and int(instance.state_id) == 9 and instance.final_classification is not None and instance.final_classification.signal_name is not None and instance.final_classification.signal_name.lower() == \
            "executive movement":
            etl_executive_obj.insert_or_update_record(instance)

post_save.connect(etl_executive_movement, sender=TaggedNews)
