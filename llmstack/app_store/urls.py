from django.urls import path

from . import apis

urlpatterns = [
    path("api/store/search", apis.AppStoreSearchViewSet.as_view({"get": "list"})),
    path("api/store/apps", apis.AppStoreAppViewSet.as_view({"get": "list", "post": "create"})),
    path("api/store/apps/<str:slug>", apis.AppStoreAppViewSet.as_view({"get": "get"})),
    path(
        "api/store/categories",
        apis.ListAppStoreCategories.as_view(),
    ),
    path(
        "api/store/categories/recommended/<str:slug>/apps",
        apis.AppStoreSpecialCategoryAppsViewSet.as_view({"get": "recommended_apps"}),
    ),
    path(
        "api/store/categories/new/apps",
        apis.AppStoreSpecialCategoryAppsViewSet.as_view({"get": "new_apps"}),
    ),
    path(
        "api/store/categories/my-apps/apps",
        apis.AppStoreSpecialCategoryAppsViewSet.as_view({"get": "my_apps"}),
    ),
    path("api/store/categories/<str:slug>/apps", apis.AppStoreCategoryAppsViewSet.as_view({"get": "list"})),
]
