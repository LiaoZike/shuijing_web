from django.contrib import admin
from .models import HeroSlide, ServiceItem, Activity

#################################################
# Admin:首頁輪播資料管理
#################################################
@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display  = ['order', 'category', 'title', 'is_active']
    list_editable = ['order', 'is_active']
    list_display_links = ['title']
    list_filter   = ['category', 'is_active']

#################################################
# Admin:首頁服務項目管理
##################################################
@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display       = ['order', 'icon', 'title', 'is_featured', 'is_active']
    list_display_links = ['title']
    list_editable      = ['order', 'is_featured', 'is_active']
    list_filter        = ['is_featured', 'is_active']
 
###############################################
# Admin:活動資料管理
################################################
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display       = ['date', 'title', 'location', 'is_featured', 'is_active']
    list_display_links = ['title']
    list_editable      = ['is_featured', 'is_active']
    list_filter        = ['is_active', 'is_featured']
    date_hierarchy     = 'date'
 
    # 編輯頁分群
    fieldsets = [
        ('基本資訊', {
            'fields': ['title', 'title_2', 'description', 'cover_image']
        }),
        ('時間地點', {
            'fields': ['date', 'end_date', 'time', 'location']
        }),
        ('聯絡資訊', {
            'fields': ['contact_name', 'contact_phone', 'contact_email'],
            'classes': ['collapse'],   # 預設收合
        }),
        ('設定', {
            'fields': ['link_url', 'is_featured', 'is_active']
        }),
    ]