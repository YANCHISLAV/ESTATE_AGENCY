from django.contrib import admin
from .models import *






class RealtyOwnerInline(admin.TabularInline):
    model = Realty
    fk_name = "owner"
    verbose_name = "Realties in which user owner"

class RealtyLandlordInline(admin.TabularInline):
    model = Realty
    fk_name = "landlord"
    verbose_name = "Realties in which user loadlord"

class QueryOwnerInline(admin.TabularInline):
    model = Query
    fk_name = "owner"
    verbose_name = "Queries, which user send"

class QueryLandlordInline(admin.TabularInline):
    model = Query
    fk_name = "landlord"
    verbose_name = "Queries, which user get"

class RealtyAddresInline(admin.TabularInline):
    model = Realty
    fk_name = "address"
    verbose_name = "Realties with this address"

class RealtyCategoryInline(admin.TabularInline):
    model = Realty
    fk_name = "cat"
    verbose_name = "Realties with this category"

class QueryRealtyInline(admin.TabularInline):
    model = Query
    fr_name = "realty"
    verbose_name = "Queries with this realty"


class TransactionRealtyInline(admin.TabularInline):
    model = Transaction
    fr_name = "realty"
    verbose_name = "Transactions with this realty"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('display_status','username','first_name','last_name', 'date', 'phone_number', 'photo')
    inlines = [RealtyOwnerInline, RealtyLandlordInline, QueryLandlordInline,QueryOwnerInline]
    list_filter = ('is_superuser',)
    ordering = ('-date',)




@admin.register(Realty)
class Realty(admin.ModelAdmin):
    list_display = ('name', 'price', 'cat', 'owner', 'landlord', 'created_at','updated_at', 'rented_at', 'is_sold')
    list_filter = ('cat', 'owner', 'landlord', 'is_sold')
    ordering = ('-created_at',)
    inlines = [QueryRealtyInline, TransactionRealtyInline]


@admin.register(Address)
class Address(admin.ModelAdmin):
    list_display = ('state', 'city', 'address')
    inlines =[RealtyAddresInline]


@admin.register(Category)
class Category(admin.ModelAdmin):
    list_display = ('name', )
    inlines =[RealtyCategoryInline]


@admin.register(Query)
class Query(admin.ModelAdmin):
    list_display = ('realty', 'owner', 'landlord')



@admin.register(Transaction)
class Transaction(admin.ModelAdmin):
    list_display = ('realty', 'price')


admin.site.register(InformationCompany)
admin.site.register(PrivacyPolicy)
admin.site.register(PromoCode)
admin.site.register(Question)
admin.site.register(Vacancy)
admin.site.register(Review)
admin.site.register(Article)
admin.site.register(Answer)

