from django.contrib import admin
from .models import (HeroSlide, ServiceItem, Activity, Registration, Participant, ContactMessage,
                     AiotProject, UsrAchievement, UsrVideo, UsrVideoImage, UsrTeamMember, Notice, NoticeImage)
from django.db import models
from django.forms import Textarea, ModelForm, TextInput
admin.site.site_header = "風雲客棧管理系統"
admin.site.site_title = "風雲客棧管理後台"
admin.site.index_title = "歡迎使用風雲客棧管理系統"     

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
        'is_featured', 'allow_waitlist', 'is_active','is_registration_closed'
    ]
    list_editable = ['is_featured', 'allow_waitlist', 'is_active']
    list_filter   = ['is_active', 'is_featured', 'allow_waitlist', 'is_registration_closed']
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
            'fields': ('link_url', 'max_participants','max_per_user', 'allow_waitlist')
        }),
        ('聯絡資訊', {
            'fields': ('contact_name', 'contact_phone', 'contact_email')
        }),
        ('狀態', {
            'fields': ('is_featured','is_registration_closed','is_active')
        }),
    )



##################################################
class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    inlines       = [ParticipantInline]
    list_display  = ['activity', 'name', 'phone', 'participant_count', 'status', 'created_at']
    list_editable = ['status']
    list_filter   = ['activity', 'status']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']
    ordering      = ['-created_at']

    
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display       = ['created_at', 'name', 'email', 'subject', 'status']
    list_display_links = [ 'name', 'email','subject']
    list_editable      = ['status']
    list_filter        = ['status']
    search_fields      = ['name', 'email', 'subject']
    readonly_fields    = ['name', 'email', 'phone', 'subject', 'message', 'created_at']
    ordering           = ['-created_at']

@admin.register(AiotProject)
class AiotProjectAdmin(admin.ModelAdmin):
    list_display = ['order', 'icon', 'title', 'tags', 'is_active']
    list_display_links = ['title']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'tags']

@admin.register(UsrAchievement)
class UsrAchievementAdmin(admin.ModelAdmin):
    list_display = ['date', 'category', 'title', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description']

class UsrVideoImageInline(admin.StackedInline):
    model = UsrVideoImage
    extra = 1

class UsrVideoAdminForm(ModelForm):
    class Meta:
        model = UsrVideo
        fields = '__all__'
        widgets = {
            'description': Textarea(attrs={'rows': 4}),
            'embed_code': Textarea(attrs={
                'rows': 4,
                'placeholder': '貼入 <iframe src="..."> 原始碼（來自 YouTube / Facebook / 其他平台）',
                'style': 'font-family: monospace; font-size: 12px; width: 100%;'
            }),
            'link_url': TextInput(attrs={
                'placeholder': 'https://www.youtube.com/watch?v=XXXXXXX',
                'style': 'width: 100%;'
            }),
        }

@admin.register(UsrVideo)
class UsrVideoAdmin(admin.ModelAdmin):
    form = UsrVideoAdminForm
    list_display = ['date', 'title', 'is_active']
    list_editable = ['is_active']
    search_fields = ['title']
    # save_on_top = True
    inlines = [UsrVideoImageInline]

    fieldsets = (
        ('基本資訊', {
            'fields': ('date', 'title', 'description')
        }),
        ('影音來源（三選一填寫即可）', {
            'description': '⚠️ 優先順序：① 上傳影片檔 ＞ ② 自訂嵌入碼 ＞ ③ YouTube 連結',
            'fields': ('video_file', 'embed_code', 'link_url'),
        }),
        ('顯示設定', {
            'fields': ('is_active',)
        }),
    )


class NoticeImageInline(admin.TabularInline):
    model = NoticeImage
    extra = 1

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['publish_date', 'category', 'title', 'is_priority', 'is_active']
    list_filter = ['category', 'is_active', 'is_priority']
    search_fields = ['title', 'content']
    list_editable = ['is_active', 'is_priority']
    date_hierarchy = 'publish_date'
    inlines = [NoticeImageInline]

@admin.register(UsrTeamMember)
class UsrTeamMemberAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'role', 'is_active']
    list_display_links = ['name']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'role', 'description']
