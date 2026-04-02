from django.contrib import admin
from .models import HeroSlide, ServiceItem, Activity, Registration, Participant

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
    list_display  = [
        'title', 'date', 'end_date',
        'register_deadline', 'location',
        'is_registration_open', 'is_past',
        'is_featured', 'is_active'
    ]
    list_editable = ['is_featured', 'is_active']
    list_filter   = ['is_active', 'is_featured']
    search_fields = ['title', 'location', 'tags', 'contact_name']
    ordering      = ['date']

    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'title_2', 'tags', 'description', 'cover_image')
        }),
        ('時間地點', {
            'fields': ('date', 'end_date', 'register_deadline', 'time', 'location')
        }),
        ('報名設定', {
            'fields': ('link_url', 'max_participants')
        }),
        ('聯絡資訊', {
            'fields': ('contact_name', 'contact_phone', 'contact_email')
        }),
        ('狀態', {
            'fields': ('is_active', 'is_featured')
        }),
    )



##################################################
class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    inlines       = [ParticipantInline]
    list_display  = ['activity', 'name', 'phone', 'participant_count', 'created_at']
    list_filter   = ['activity']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']
    ordering      = ['-created_at']