# Django问题
1. TypeError: as_view() takes 1 positional argument but 2 were given
    - location:
        ```
        urlpatterns = [
            path('logout/', auth_views.LogoutView.as_view, {'template_name': 'account/logout.html'}, name='user_logout'),
        ]
        ```
    - resolve:
        ```
        as_view在path中使用时，必须以as_view()的形式，否则会报错
        ```