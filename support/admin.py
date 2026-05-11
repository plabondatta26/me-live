from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import SupportPost,SupportPostReply,SupportPostImage

class PostImageInline(admin.StackedInline):
    model = SupportPostImage
    readonly_fields = ['post_image','image',]

    def post_image(self, obj):
        return mark_safe('<img src="{url}" width="200" />'.format(
                url = obj.image.url,
                width=obj.image.width,
                height=obj.image.height,
            )
        )

class SupportPostReplyInline(admin.StackedInline):
    model = SupportPostReply

@admin.register(SupportPost)
class  PostAdmin(admin.ModelAdmin):
    inlines = [PostImageInline,SupportPostReplyInline ]
    list_display = [
        'get_uid',
        'text',
        'get_images_count',
        'get_replies_count',
        'created_datetime',

    ]
    list_display_links = ['get_uid','get_images_count','get_replies_count']
    readonly_fields = ['user','text',]
    # search_fields = ['title','slug']

    def get_uid(self, obj):
        return obj.user.id

    get_uid.short_description = 'User ID'

    def get_images_count(self, obj):
        return obj.support_post_images.count()

    get_images_count.short_description = 'Images'

    def get_replies_count(self, obj):
        return obj.support_post_replies.count()

    get_replies_count.short_description = 'Replies'
