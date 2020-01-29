from django.contrib import admin
from .models import *


# Register your models here.

class Data_Point_Inline(admin.TabularInline):
    """

    """
    model = Data_Point


class Data_Set_Inline(admin.StackedInline):
    """

    """
    model = Data_Set


class US_County_Inline(admin.TabularInline):
    """

    """
    model = US_County


@admin.register(US_State)
class US_State_Admin(admin.ModelAdmin):
    """
    US_State model representation in admin interface
    """
    inlines = (US_County_Inline,)


@admin.register(US_County)
class US_Counties_Admin(admin.ModelAdmin):
    """
    US_Counties model representation in admin interface
    """
    inlines = (Data_Point_Inline,)


@admin.register(Health_Indicator)
class Health_Indicator_Admin(admin.ModelAdmin):
    """
     Health_Indicator model representation in admin interface
    """
    inlines = (Data_Set_Inline,)


@admin.register(Document)
class Document_Admin(admin.ModelAdmin):
    """
    Document model representation in admin interface
    """
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)


@admin.register(Data_Set)
class Data_Set_Admin(admin.ModelAdmin):
    """
    Data_Set model representation in admin interface
    """
    search_fields = ('indicator__name',)
    inlines = (Data_Point_Inline,)


@admin.register(Data_Point)
class Data_Point_Admin(admin.ModelAdmin):
    """
    Data_Points model representation in admin interface
    """
    search_fields = ('county__name', 'county__state__name',)
