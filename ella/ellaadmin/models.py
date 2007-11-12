from django.db import models, connection
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ugettext

from ella.core.models import Category

#@cache_this
def has_permission(user, obj, category, perm_code):
    qn = connection.ops.quote_name

    group_perms = Group._meta.get_field('permissions').m2m_db_table()
    perm = Permission.objects.get(content_type=ContentType.objects.get_for_model(obj), codename=perm_code)

    if user.has_perm(perm_code):
        return True

    if CategoryUserRole.objects.filter(category=category, user=user).extra(
                tables=(group_perms,),
                where=(
                    '%s.group_id = %s.group_id' % (qn(group_perms), qn(CategoryUserRole._meta.db_table)),
                    '%s.permission_id = %s' % (qn(group_perms), perm.id)
),
).count():
        return True

    if SiteUserRole.objects.filter(site=category.site_id, user=user).extra(
                tables=(group_perms,),
                where=(
                    '%s.group_id = %s.group_id' % (qn(group_perms), qn(SiteUserRole._meta.db_table)),
                    '%s.permission_id = %s' % (qn(group_perms), perm.id)
),
).count():
        return True

    return False

def applicable_sites(user, permission=None):
    group_perms = Group._meta.get_field('permissions').m2m_db_table()
    enable_site_table = SiteUserRole._meta.db_table
    qn = connection.ops.quote_name

    q = SiteUserRole.objects.filter(user=user).extra(
                        tables=(group_perms,),
                        where=(
                            '%s.group_id = %s.group_id' % (qn(group_perms), qn(enable_site_table)),
)
).distinct().values('site')
    if permission:
        app_label, code = permission.split('.', 1)
        perm = Permission.objects.get(content_type__app_label=app_label, codename=code)
        q = q.extra(
                where=('%s.permission_id = %s' % (qn(group_perms), perm.id),)
)
    return [ d['site'] for d in q ]



def applicable_categories(user, permission=None):
    group_perms = connection.ops.quote_name(Group._meta.get_field('permissions').m2m_db_table())
    enable_cat_table = connection.ops.quote_name(CategoryUserRole._meta.db_table)
    qn = connection.ops.quote_name


    q = CategoryUserRole.objects.filter(user=user).extra(
                        tables=(group_perms,),
                        where=(
                            '%s.group_id = %s.group_id' % (qn(group_perms), qn(enable_cat_table)),
)
).distinct().values('category')

    if permission:
        app_label, code = permission.split('.', 1)
        perm = Permission.objects.get(content_type__app_label=app_label, codename=code)
        q = q.extra(
                where=('%s.permission_id = %s' % (qn(group_perms), perm.id),)
)

    return [ d['category'] for d in q ]

class CategoryUserRole(models.Model):
    """
    Apply all group's permission for the given user to this category.
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    category = models.ForeignKey(Category)

    def __unicode__(self):
        return ugettext(u'User %(user)s is a %(group)s for %(category)s.') % {
                'user' : self.user,
                'group' : self.group,
                'category' : self.category,
}

    class Meta:
        verbose_name = _("User role in category")
        verbose_name_plural = _("User roles in categories")

class SiteUserRole(models.Model):
    """
    Apply all group's permission for the given user to this site.
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    site = models.ForeignKey(Site)

    def __unicode__(self):
        return ugettext(u'User %(user)s is a %(group)s for %(site)s.') % {
                'user' : self.user,
                'group' : self.group,
                'site' : self.site,
}

    class Meta:
        verbose_name = _("User role in site")
        verbose_name_plural = _("User roles in site")

class SiteUserRoleOptions(admin.ModelAdmin):
    list_filter = ('user', 'group', 'site',)
    list_display = ('user', 'group', 'site',)

class CategoryUserRoleOptions(admin.ModelAdmin):
    list_filter = ('user', 'group', 'category',)
    list_display = ('user', 'group', 'category',)

admin.site.register(CategoryUserRole, CategoryUserRoleOptions)
admin.site.register(SiteUserRole, SiteUserRoleOptions)
