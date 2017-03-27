from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User

def get_or_set_owner_permission(group_id, group_name):
    content_type = ContentType.objects.get_for_model(User)
    codename = 'is_owner_' + str(group_id)
    if not Permission.objects.filter(content_type=content_type, codename=codename):
        permission = Permission.objects.create(
                content_type=content_type,
                codename=codename,
                name="Is owner of " + group_name
        )
        permission.save()
        return permission
    else:
        return Permission.objects.get(content_type=content_type, codename=codename)

def try_permission_query(model, codename):
    content_type = ContentType.objects.get_for_model(model)
    return Permission.objects.filter(content_type=content_type, codename=codename)
