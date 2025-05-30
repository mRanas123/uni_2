from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, City, Address, Order, Offer, Complaint, Rating

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'display_user_type', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'birth_date', 
                                    'gender', 'phone', 'photo', 'work_experience')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 
                                   'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)
    
    def display_user_type(self, obj):
        return obj.get_user_type_display()
    display_user_type.short_description = 'User Type'

class OfferInline(admin.TabularInline):
    model = Offer
    extra = 0
    fields = ('worker', 'status', 'price', 'company_paid', 'expected_date')
    readonly_fields = ('last_time_date',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'budget', 'created_date', 'get_status_display')
    list_filter = ('status', 'created_date')
    search_fields = ('customer__email', 'customer__first_name', 'customer__last_name')
    inlines = [OfferInline]
    list_select_related = ('customer',)

class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order', 'rate', 'created_at')
    list_filter = ('rate', 'created_at')
    search_fields = ('user__email', 'order__id')
    raw_id_fields = ('order',)

class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_type_display', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('user__email', 'message')

admin.site.register(User, CustomUserAdmin)
admin.site.register(City)
admin.site.register(Address)
admin.site.register(Order, OrderAdmin)
admin.site.register(Offer)
admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(Rating, RatingAdmin)